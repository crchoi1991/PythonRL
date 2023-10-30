import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# 데이터셋 경로와 파라미터 설정
train_data_path = './Training1'
val_data_path = './Validation1'
image_size = (256, 256)
batch_size = 32
num_classes = 2  # 정상과 비정상 2개의 클래스

# 데이터 로드와 전처리
datagen = ImageDataGenerator(rescale=1./255)

train_data = datagen.flow_from_directory(
	train_data_path,
    target_size=image_size,
    batch_size=batch_size,
    class_mode='binary',  # 이진 분류 설정
    shuffle=True
)

val_data = datagen.flow_from_directory(
	val_data_path,
    target_size=image_size,
    batch_size=batch_size,
    class_mode='binary',  # 이진 분류 설정
    shuffle=False
)
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense

# 모델 생성
model = Sequential()
model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(256, 256, 3)))
model.add(MaxPooling2D((2, 2)))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D((2, 2)))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(Flatten())
model.add(Dense(64, activation='relu'))
model.add(Dense(1, activation='sigmoid'))  # 이진 분류 문제이므로 마지막에 sigmoid 활성화 함수 사용

# 모델 컴파일
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 모델 학습
model.fit(train_data, epochs=10, validation_data=val_data)

