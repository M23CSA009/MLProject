# -*- coding: utf-8 -*-
"""M23CSA009_DLOps_ClassAssignment_2_Q_1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SN6bXJhlkc3PjI8gCfF1Ps-sam7viL-j
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split
from torch.utils.tensorboard import SummaryWriter
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

#designing the dataloader

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

train_dataset = datasets.USPS(root='./data', train=True, download=True, transform=transform)
test_dataset = datasets.USPS(root='./data', train=False, download=True, transform=transform)

batch_size = 64

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

#MLP based classifier

class MLP(nn.Module):
    def __init__(self):
        super(MLP, self).__init__()
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(16*16, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 10)

    def forward(self, x):
        x = self.flatten(x)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

#CNN based classifier

class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()

        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(32, 64, kernel_size=3, stride=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

#functions for training and testing the model on the MLP and CNN

def train(model, train_loader, criterion, optimizer, epoch, writer):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % 100 == 0:
            print(f'Train Epoch: {epoch} [{batch_idx * len(data)}/{len(train_loader.dataset)}'
                  f' ({100. * batch_idx / len(train_loader):.0f}%)]\tLoss: {loss.item():.6f}')
            writer.add_scalar('training loss', loss.item(), epoch * len(train_loader) + batch_idx)


def test(model, test_loader, criterion, epoch, writer):
    model.eval()
    test_loss = 0
    correct = 0
    y_true = []
    y_pred = []
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += criterion(output, target).item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
            y_true.extend(target.cpu().numpy())
            y_pred.extend(pred.cpu().numpy().flatten())

    test_loss /= len(test_loader.dataset)
    accuracy = (correct / len(test_loader.dataset)) * 100
    precision = precision_score(y_true, y_pred, average='macro')
    recall = recall_score(y_true, y_pred, average='macro')
    cnf_matrix = confusion_matrix(y_true, y_pred)
    # print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%), Precision: {:.4f}, Recall: {:.4f}\n'
    #       .format(test_loss, correct, len(test_loader.dataset),
    #               100. * accuracy, precision, recall))
    print(f'\n Test set: Average Loss : {test_loss:.4f} accuracy : {accuracy:.4f}% precision : {precision:.4f} Recall : {recall:.4f}')
    writer.add_scalar('test loss', test_loss, epoch)
    writer.add_scalar('accuracy', accuracy, epoch)
    writer.add_scalar('precision', precision, epoch)
    writer.add_scalar('recall', recall, epoch)
    return cnf_matrix

#mainloop for training and testing the MLP and the CNN

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    mlp_model = MLP().to(device)
    cnn_model = CNN().to(device)

    criterion = nn.CrossEntropyLoss()

    mlp_optimizer = optim.Adam(mlp_model.parameters(), lr=0.001)
    cnn_optimizer = optim.Adam(cnn_model.parameters(), lr=0.001)

    mlp_writer = SummaryWriter('runs/mlp')
    cnn_writer = SummaryWriter('runs/cnn')

    num_epochs = 50

    for epoch in range(1, num_epochs + 1):
        print(f'::::::::::::: EPOCH {epoch} :::::::::::::')
        print("MLP model :")
        train(mlp_model, train_loader, criterion, mlp_optimizer, epoch, mlp_writer)
        mlp_confusion = test(mlp_model, test_loader, criterion, epoch, mlp_writer)
        print("CNN Model :")
        train(cnn_model, train_loader, criterion, cnn_optimizer, epoch, cnn_writer)
        cnn_confusion = test(cnn_model, test_loader, criterion, epoch, cnn_writer)

    mlp_writer.close()
    cnn_writer.close()

    # Print final confusion matrices
    print("MLP Confusion Matrix:")
    print(mlp_confusion)
    print("CNN Confusion Matrix:")
    print(cnn_confusion)


if __name__ == '__main__':
    main()

# Commented out IPython magic to ensure Python compatibility.
# %load_ext tensorboard

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir runs