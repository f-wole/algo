import os
import sys
import pickle
import configparser
import pandas as pd
from ast import literal_eval
from utils import model_lstm,model_mix
from keras.callbacks import EarlyStopping,ModelCheckpoint,ReduceLROnPlateau
import matplotlib.pyplot as plt

train_path=sys.argv[1]
valid_path=sys.argv[2]
out_dir=sys.argv[3]
profile=sys.argv[4]
batch=int(sys.argv[5])
window=int(sys.argv[6])

if not train_path.endswith("/"):
    train_path+="/"
if not valid_path.endswith("/"):
    valid_path+="/"
if not out_dir.endswith("/"):
    out_dir=out_dir+"/"
model_type=profile.split("_")[1]
model_path=out_dir+"model_"+model_type+".h5"

# load data
with open(train_path+"data.pkl","rb") as r:
    X_train, y_train = pickle.load(r)[:2] # load train from train_path
with open(valid_path+"data.pkl","rb") as r:
    X_valid, y_valid = pickle.load(r)[:2] # load valid from valid_path
features = X_valid.shape[2] # get number of features

print("# X_train: ",X_train.shape)
print("# y_train: ",y_train.shape)
print("# X_valid: ",X_valid.shape)
print("# y_valid: ",y_valid.shape)


# Inizialize model

if model_type not in ["lstm","mix"]:
    print("Error: model_type can be either 'lstm' or 'mix'")
    exit(1)
config = configparser.RawConfigParser()
config.read(profile)
if model_type=="lstm":
    lstm1 = int(config.get('NetworkProperties', 'lstm1'))
    lstm2 = int(config.get('NetworkProperties', 'lstm2'))
    dense = int(config.get('NetworkProperties', 'dense'))
    drop_out = float(config.get('NetworkProperties', 'drop_out'))
    n_epochs = int(config.get('NetworkProperties', 'n_epochs'))
    lr = float(config.get('NetworkProperties', 'lr'))
    rop = config.get('NetworkProperties', 'rop') in ["true","True"]
    es = config.get('NetworkProperties', 'es') in ["true", "True"]
    mcp = config.get('NetworkProperties', 'mcp') in ["true", "True"]
    patience = int(config.get('NetworkProperties', 'patience'))

    model=model_lstm(window, features,lstm1,lstm2,dense,drop_out,lr)

if model_type=="mix":
    filters=int(config.get('NetworkProperties', 'filters'))
    ksize=int(config.get('NetworkProperties', 'ksize'))
    lstm1 = int(config.get('NetworkProperties', 'lstm1'))
    lstm2 = int(config.get('NetworkProperties', 'lstm2'))
    dense = int(config.get('NetworkProperties', 'dense'))
    drop_out = float(config.get('NetworkProperties', 'drop_out'))
    n_epochs = int(config.get('NetworkProperties', 'n_epochs'))
    lr = float(config.get('NetworkProperties', 'lr'))
    rop = config.get('NetworkProperties', 'rop') in ["true","True"]
    es=config.get('NetworkProperties', 'es') in ["true","True"]
    mcp=config.get('NetworkProperties', 'mcp') in ["true","True"]
    patience=int(config.get('NetworkProperties', 'patience'))

    model=model_mix(window, features,filters,ksize,lstm1,lstm2,dense,drop_out,lr)

learning_rate_reduction = ReduceLROnPlateau(monitor='loss', patience=25, verbose=1,factor=0.25, min_lr=0.00001)
early_stopping=EarlyStopping(monitor="val_loss",patience=patience,min_delta=0.0001)
model_ckpt=ModelCheckpoint(monitor="val_loss",save_best_only=True,mode="auto",filepath=model_path)
callbacks=[]
if rop:
    callbacks.append(learning_rate_reduction)
if es:
    callbacks.append(early_stopping)
if mcp:
    callbacks.append(model_ckpt)


# Train

history_lstm=model.fit(X_train,y_train,epochs=n_epochs, batch_size=batch, validation_data=(X_valid, y_valid),
                       verbose=1, callbacks=callbacks,shuffle=False)

plt.plot(history_lstm.history['loss'])
plt.plot(history_lstm.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'valid'], loc='upper right')
plt.savefig(out_dir+"train_plot.png")

log={key:history_lstm.history[key] for key in ["loss","val_loss"]}
df=pd.DataFrame(log)
df.to_excel(out_dir+"train_log.xlsx")

if not mcp:
    model.save(model_path)

y_pred=model.predict(X_train)
plt.close()
plt.figure(figsize=(30,10))
plt.plot(y_train[1:], label="actual")
plt.plot(y_pred[1:], label="prediction lstm")

plt.legend(fontsize=20)
plt.grid(axis="both")
plt.title("Train",fontsize=25)
plt.savefig(out_dir+"train_pred.png")
