#Code December 1st
#Cost 1, 1.8, 2.5

import tensorflow as tf
import cvxpy as cp
import keras
import numpy as np
import matplotlib.pyplot as plt
#from util import *
import random
import csv
random.seed(32)
from sklearn.metrics import mean_squared_error
from keras.layers import Dense, Dropout, Activation, Flatten
from sklearn.metrics import mean_squared_error
from keras.constraints import non_neg
import time
import os
from keras.models import Sequential  # formulating NN model
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
from tensorflow.python.framework import graph_util
from keras.models import load_model

batch_size = 20
learning_rate = 0.001
training_epochs = 50
num_of_buses = 14


def scaled_gradient(x, predictions):
    grad, = tf.gradients(predictions, x)  # tf.gradients([z1, z2], [w1, w2, w3], grad_ys=[[w for z1], [w for z2]])
    return grad

def normal_model(input_dim, output_dim):
    input = keras.layers.Input(shape=(input_dim,))
    x0 = keras.layers.Dense(80, activation='relu')(input)
    x1 = keras.layers.Dense(50, activation='relu')(x0)
    x2 = keras.layers.Dense(30, activation='relu')(x1)
    out = keras.layers.Dense(output_dim, kernel_constraint=non_neg())(x2)
    model = keras.models.Model(inputs=input, outputs=out)
    return model


def keras_model_dnn(input_dim, output_dim):
    model = Sequential()
    model.add(Dense(100, input_dim=input_dim))
    model.add(Activation('relu'))
    model.add(Dense(50))
    model.add(Activation('relu'))
    model.add(Dense(30))
    model.add(Activation('relu'))
    model.add(Dense(output_dim))
    return model

with open('linear_data_all14_UC.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    rows = [row for row in reader]
    data_all = np.array(rows, dtype=float)

# with open('line_constraint14_s3.csv', 'r') as csvfile:
#     reader = csv.reader(csvfile)
#     rows = [row for row in reader]
#     constraint_all = np.array(rows, dtype=float)

print("data shape", np.shape(data_all))
X = data_all[:data_all.shape[0], :num_of_buses]  # load
Y = data_all[:data_all.shape[0], -1]  # cost

#X = data_all[10000:13000, :num_of_buses]
#Y = data_all[10000:13000, -1]
print("The last data sample instance", X[-1])

max_valuex = np.max(X, axis=0)
min_valuex = np.min(X, axis=0)
max_valuey = np.max(Y, axis=0)
min_valuey = np.min(Y, axis=0)

train_X = (np.copy(X) - min_valuex) / (max_valuex - min_valuex)  # normalization
train_Y = (np.copy(Y) - min_valuey) / (max_valuey - min_valuey)

print("Training x maximum", max_valuex)
print("Training x minimum", min_valuex)
print("Training y maximum", max_valuey)
print("Training y minimum", min_valuey)

num_samples = train_X.shape[0]
index = np.arange(num_samples)

X_train = np.copy(train_X[index[:int(0.8*num_samples)]])  # num_train=0.8*num_samples
Y_train = np.copy(train_Y[index[:int(0.8*num_samples)]])
test_X = np.copy(train_X[index[int(0.8*num_samples):]])   # num_test=0.2*num_samples
test_Y = np.copy(train_Y[index[int(0.8*num_samples):]])

x_val = tf.placeholder(tf.float32, shape=(None, num_of_buses), name="load")
#l_val = tf.placeholder(tf.float32, shape=(None, num_of_buses))
y_val = tf.placeholder(tf.float32, shape=(None, 1))
cost_vec = tf.placeholder(tf.float32, shape=(None, num_of_buses))

#Trial for keras model
model = keras_model_dnn(input_dim=num_of_buses, output_dim=1)
predictions = model(x_val)
sess = tf.Session()
cost = tf.reduce_sum(tf.pow(predictions - y_val, 2)) / (2 * batch_size)
grad_pre = tf.gradients(predictions, x_val)

loss = tf.reduce_mean(tf.square(predictions - y_val))

optimizer = tf.train.AdamOptimizer(learning_rate).minimize(loss)  # ??????????????????

init = tf.global_variables_initializer()
saver = tf.train.Saver()
with tf.Session() as sess:
    # Initializing the Variables
    sess.run(init)
    #keras.bakend.set_session(sess)
    model.compile(loss='mean_absolute_error', optimizer='adam')
    #model.load_weights('NN_convex_14.h5')
    model.fit(X_train, Y_train, batch_size=32, epochs=30, shuffle=True)  # validation_split=0.1 ????????????

    pred_val = model.predict(test_X)

    RMSE = mean_squared_error(pred_val[:200], test_Y[:200])

    plt.plot(pred_val[:200], 'r', linewidth=3)
    plt.plot(test_Y[:200], 'b')
    plt.show()  # ??????????????????

    for epoch in range(training_epochs):
        #start_time = time.time()
        for iterations in range(int(num_samples*0.8/batch_size-1)):
            _x = X_train[iterations*batch_size:(iterations+1)*batch_size]  #batch
            _y = Y_train[iterations*batch_size:(iterations+1)*batch_size].reshape(-1, 1)
            sess.run(optimizer,
                     feed_dict={x_val: _x, y_val: _y})
        if (epoch + 1) % 2 == 0:
            c = sess.run(cost, feed_dict={x_val: _x, y_val: _y})  # calculate total y error
            print("Epoch", (epoch + 1), "cost loss= ", c)
    model.save_weights('model14.h5')

    pred_val=sess.run(predictions, feed_dict={x_val: test_X})

    RMSE = mean_squared_error(pred_val[:200], test_Y[:200])

    plt.plot(pred_val[:200], 'r', linewidth=3)
    plt.plot(test_Y[:200], 'b')  # ????????????
    plt.show()

    time_all = []

    num = 0
    cost_record = []
    for i in range(0,  num_samples):  # Starting sample: 500, 900, 24380
        current_x = np.copy(train_X[i]).reshape(1, -1)
        #print("Current load", current_x * max_valuex)
        #print("original costs", train_Y[i] * max_valuey)
        #print("Predicted costs", (sess.run(predictions, feed_dict={x_val: current_x})) * (max_valuey))
        # print("Current load", current_x * (max_valuex - min_valuex) + min_valuex)
        # print("original costs", train_Y[i] * (max_valuey - min_valuey) + min_valuey)
        # print("Predicted costs", (sess.run(predictions, feed_dict={x_val: current_x})) * (max_valuey - min_valuey) + min_valuey)
        # print("next cost", train_Y[i+1])
        cost_record.append((sess.run(predictions, feed_dict={x_val: current_x})) * (max_valuey - min_valuey) + min_valuey)
        num += 1

    e = 0.01
    # print(np.sum(current_x))
    # print(current_x)
    load = current_x
    # print(load)
    # cost_max_0 = (sess.run(predictions, feed_dict={x_val: current_x})) * (max_valuey - min_valuey) + min_valuey
    cost_max_0 = 0.1
    cost_max_1 = 0
    # print(cost_max_0-cost_max_1)
    status_limit = 0
    k = 0
    percentage = 1
    r = 0
    l_center = 15*(1+r) / num_of_buses
    while (cost_max_0 - cost_max_1) >= 0.0001 and k <= 5000:
        k += 1
        cost_max_1 = cost_max_0
        grad_0 = sess.run(grad_pre, feed_dict={x_val: load})
        grad_0 = np.array(grad_0)
        index = np.argsort(grad_0)
        index = index[0][0]
        grad_status = 0
        for i in index[::-1]:
            if (load[0][i]) * (max_valuex[i] - min_valuex[i]) + min_valuex[i] + e <= l_center + percentage * l_center:
                load[0][i] = (((load[0][i]) * (max_valuex[i] - min_valuex[i]) + min_valuex[i] + e) - min_valuex[i]) / (
                            max_valuex[i] - min_valuex[i])
                grad_status = 1
                break
            else:
                status_limit += 1
        for j in index:
            if grad_status == 0:
                break
            elif load[0][j] * (max_valuex[j] - min_valuex[j]) + min_valuex[j] - e >= l_center - percentage * l_center:
                load[0][j] = ((load[0][j] * (max_valuex[j] - min_valuex[j]) + min_valuex[j] - e) - min_valuex[j]) / (
                            max_valuex[j] - min_valuex[j])
                break
            else:
                status_limit += 1

        cost_max_0 = (sess.run(predictions, feed_dict={x_val: load})) * (max_valuey - min_valuey) + min_valuey
        # print(cost_max_0)
        cost_max_0 = (cost_max_0[0])[0]
    print(cost_max_0)
    print(k)
    print(status_limit)
    print(max(cost_record))
    print(min(cost_record))
    print(load * (max_valuex - min_valuex) + min_valuex)
    print(max_valuey, min_valuey)
    with open('linear_load_test.csv', 'w', newline='') as f:
         writer = csv.writer(f)
         writer.writerows(current_x * (max_valuex - min_valuex) + min_valuex)