#-----------------------------------------------------#
#                   Library imports                   #
#-----------------------------------------------------#
#External libraries
from segmentation_models import Unet
from keras.models import model_from_json
import numpy
import math
#Internal libraries/scripts
import inputreader as CNNsolver_IR

#-----------------------------------------------------#
#                    Fixed Parameter                  #
#-----------------------------------------------------#
image_shape = (512, 512, 1)
batch_size = 30
max_queue_size = 10
epochs = 1


#-----------------------------------------------------#
#                Neural Network - Class               #
#-----------------------------------------------------#
class NeuralNetwork:
    # Initialize class variables
    model = None

    # Create a Convolutional Neural Network with Keras
    def __init__(self):
        model = Unet(backbone_name='resnet34', encoder_weights=None,
                    input_shape=image_shape, classes=3, activation='softmax')
        model.compile('Adam', 'categorical_crossentropy',
                    ['categorical_accuracy'])
        self.model = model

    # Train the Neural Network model on the provided case ids
    def train(self, ids, data_path):
        # Create a Input Reader
        reader = CNNsolver_IR.InputReader(data_path)
        # Iterate over each case
        for i in ids:
            # Load the MRI of the case
            mri = reader.case_loader(i)
            # Calculate the number of steps for the fitting
            steps = math.ceil(mri.size / batch_size)
            # Fit current MRI to the CNN model
            self.model.fit_generator(mri.generator_train(batch_size, steps),
                steps_per_epoch=steps, epochs=epochs, max_queue_size=max_queue_size)

    # Predict with the Neural Network model on the provided case ids
    def predict(self, ids, data_path):
        results = []
        # Create a Input Reader
        reader = CNNsolver_IR.InputReader(data_path)
        # Iterate over each case
        for i in ids:
            # Load the MRI of the case
            mri = reader.case_loader(i, True)
            # Calculate the number of steps for the fitting
            steps = math.ceil(mri.size / batch_size)
            # Fit current MRI to the CNN model
            pred = self.model.predict_generator(
                mri.generator_predict(batch_size, steps),
                steps=steps, max_queue_size=max_queue_size)
            # Transform probabilities to classes
            pred_seg = numpy.argmax(pred, axis=-1)
            # Add segmentation prediction to the MRI case object
            mri.add_segmentation(pred_seg, False)
            # Add the MRI to the results list
            results.append(mri)
        # Return final results
        return results

    # Evaluate the Neural Network model on the provided case ids
    def evaluate(self, ids, data_path):
        # Create a Input Reader
        reader = CNNsolver_IR.InputReader(data_path)
        # Iterate over each case
        for i in ids:
            # Load the MRI of the case
            mri = reader.case_loader(i)
            # Calculate the number of steps for the fitting
            steps = math.ceil(mri.size / batch_size)
            # Fit current MRI to the CNN model
            score1, score2 = self.model.evaluate_generator(
                mri.generator_train(batch_size, steps),
                steps=steps, max_queue_size=max_queue_size)
            print(str(i) + "\t" + str(score1) + "\t" + str(score2))

    # Dump model to file
    def dump(self, path):
        # Serialize model to JSON
        model_json = self.model.to_json()
        with open("model/model.json", "w") as json_file:
            json_file.write(model_json)
        # Serialize weights to HDF5
        self.model.save_weights("model/weights.h5")

    # Load model from file
    def load(self, path):
        # Load json and create model
        json_file = open('model/model.json', 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        self.model = model_from_json(loaded_model_json)
        # Load weights into new model
        self.model.load_weights("model/weights.h5")
        # Compile model
        self.model.compile('Adam', 'categorical_crossentropy', ['accuracy'])
