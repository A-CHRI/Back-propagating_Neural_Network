import numpy as np
import torch
from torch import nn
import matplotlib.pyplot as plt

# Initial parameters
output_neurons = 1
hidden_layers = 2 # No theoreticle reason to be more than 2
hidden_neurons = 24 # Usually 2/3 the size of the input neurons
learning_rate = 0.01
iterations = 5 #500000
days_per_segment = 21 # Usually 21 for stable stocks, and lower the more volatile
input_neurons = days_per_segment*5

# Filenames
training_files = ["data-VOO-small.csv", "data-AMD-small.csv"]
test_files = ["data-GME-small.csv"]

# Print the parameter info
print("\n Training on: " + str(training_files) + "\n Testing on: " + str(test_files))
print("\n Input neurons: " + str(input_neurons) + "\n Output neurons: " + str(output_neurons) + "\n Hidden layers: " + str(hidden_layers) + "\n Hidden neurons: " + str(hidden_neurons))
print("\n Learning rate: " + str(learning_rate) + "\n Iterations: " + str(iterations) + "\n Days per segment: " + str(days_per_segment))
print("\n Device: " + str("CUDA" if torch.cuda.is_available() else "CPU"))
input("\n Press enter to continue...")

# Initialize training data from data files
print("\Importing training data...")
training_sets = []
for i in training_files:
    training_dataImport = np.loadtxt(i, delimiter=',', skiprows=1, usecols=(1,2,3,4,5))[::-1]
    training_data = np.copy(np.transpose(training_dataImport))
    print("File " + str(i) + " imported.\nNormalizing...")

    for l in range (len(training_data[0]) - (days_per_segment + 1)):
        # Calculate x segment
        x = np.zeros(5 * days_per_segment)
        for j in range(5):
            for k in range(days_per_segment):
                x[j * days_per_segment + k] = (training_data[j, k + l] - np.mean(training_data[j,:]))/np.std(training_data[j,:])
        # Calculate y segment
        y = (training_data[0, l + days_per_segment] - np.mean(training_data[0, :]))/np.std(training_data[0,:])
        training_sets.append([x, y])
    print("Done!")

print("\Importing test data...")
# Initialize test data from data files
test_sets = []

for i in test_files:
    test_dataImport = np.loadtxt(i, delimiter=',', skiprows=1, usecols=(1,2,3,4,5))[::-1]
    test_data = np.copy(np.transpose(test_dataImport))
    print("File " + str(i) + " imported.\nNormalizing...")

    for l in range (len(test_data[0]) - (days_per_segment + 1)):
        # Calculate x segment
        x = np.zeros(5 * days_per_segment)
        for j in range(5):
            for k in range(days_per_segment):
                x[j * days_per_segment + k] = (test_data[j, k + l] - np.mean(test_data[j, :]))/np.std(test_data[j, :])
        # Calculate y segment
        y = (test_data[0, l + days_per_segment] - np.mean(test_data[0, :]))/np.std(test_data[0, :])
        test_sets.append([x, y])
    print("Done!")


# Initialize the network
print("\nInitializing network...")
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = nn.Sequential(
    nn.Linear(input_neurons, hidden_neurons),
    nn.ReLU(),
    nn.Linear(hidden_neurons, hidden_neurons),
    nn.ReLU(),
    nn.Linear(hidden_neurons, hidden_neurons),
    nn.ReLU(),
    nn.Linear(hidden_neurons, output_neurons),
).double()
model.to(device)
loss_fn = nn.MSELoss(reduction='sum')
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

Loss = np.zeros(iterations * len(training_sets))
print("Done!")


# Train the network
print("\nTraining the network... (" + str(len(training_sets)) + " segments to train on)")
training_segments = len(training_sets)
for i in range(training_segments):
    # Initialize the tensors
    x = training_sets[i][0]
    inp = torch.tensor(x, device=device).double()

    y = [training_sets[i][1]]
    outp = torch.tensor(y, device=device).double()

    for j in range(iterations):
        # Forward pass
        y_pred = model(inp)

        # Compute and print loss
        loss = loss_fn(y_pred, outp)
        print(f'Training: {int((100/training_segments) * i)}%, Segment: {i}, Iteration:{j}, Loss: {loss.item()}')
        Loss[j*(i+1)] = loss.item()

        # Zero gradients, perform a backward pass, and update the weights.
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
print("Done!")

# Test the network
print("\nTesting the network... (" + str(len(test_sets)) + " segments to test)")
test_segments = len(test_sets)
predtest = np.zeros(len(test_sets))
y_plot_pred = np.zeros(test_segments)
for i in range(test_segments):
    # Initialize the tensors
    x = test_sets[i][0]
    inp = torch.tensor(x, device=device).double()

    y = test_sets[i][1]
    outp = torch.tensor(y, device=device).double()
    print(inp)
    print(outp)
    y_pred = model(inp)
    print(y_pred)
    y_plot_pred[i] = y_pred.cpu().detach().numpy() * np.std(test_data[0, :]) + np.mean(test_data[0, :])

    # Compute and print loss
    loss = loss_fn(y_pred, outp)
    print(f'Testing: {int((100/test_segments) * i)}%, Week: {i}, Loss: {loss.item()}')
    predtest[i] = loss.item()

losspercent = 0
for i, e in enumerate(predtest):
    losspercent = losspercent + (test_sets[i][1]-e)/test_sets[i][1]

losspercent = losspercent/len(predtest)
print("Done! (" + str(losspercent) + "% loss)")

### Plotting ###
# Set up plot for the data
fig, (loss_plot, network_plot) = plt.subplots(2, 1)
fig.suptitle('Loss and Network Output')

# Set up the loss plot
loss_plot.set_ylabel("Loss function")
loss_plot.plot(Loss, label="Loss function")
loss_plot.legend()
loss_plot.grid(True)

# set up the test plot
network_plot.set_ylabel("Neural network test")
x_plot_test = np.arange(len(test_data[0]))
y_plot_test = np.array(test_data[0])
network_plot.plot(x_plot_test, y_plot_test, label='Test files daily closing price')

# Prediction data
x_plot_pred = np.arange(len(test_sets)) + days_per_segment
network_plot.plot(x_plot_pred, y_plot_pred, label='Prediction')

# Plotting
network_plot.grid(True)
network_plot.legend()
plt.show()