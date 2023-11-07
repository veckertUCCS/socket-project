# guiapp.py -> Socket Implementation
# Author: Victor Eckert
# This is the baseline for the GUI portion of our application using PyQt6

import sys
from socket_client import *

# SETUP
# Make the required imports from the PyQt6.QtWidgets library
from PyQt6.QtWidgets import (
    QApplication, 
    QLabel, 
    QWidget, 
    QPushButton,
    QLineEdit,
    QMainWindow,
    QToolBar,
    QDialog,
    QFileDialog,
    QVBoxLayout,
    QListWidget
)

# Make the required imports from the PyQt6.QtCore library
from PyQt6.QtCore import (
    QSize,
)

# BASELINE/GUI
# Instantiate the app by creating a new Window class that inherits from the
# QMainWindow parent class
class Window(QMainWindow):

    # This function initializes the application window and provides it with the necessary components
    def __init__(self):

        # Call QMainWindow's init method with a parent of none to indicate that it is the main window
        super().__init__(parent=None)
        self.is_authenticated = False
        # Set the title of the application window
        self.setWindowTitle("P-FTP-Alpha")

        # Build the layout of the home widget
        layout = QVBoxLayout()
        self.log_in_button = QPushButton("Log In")
        self.log_in_button.clicked.connect(self.authentication_function)
        layout.addWidget(self.log_in_button)
        container = QWidget()
        container.setLayout(layout)

        # Set the central widget of the application window
        self.setCentralWidget(container)

        # Set the size of the application window
        self.setFixedSize(QSize(400, 300))

        # Create a a toolbar object at the top of the window to hold relevant actions
        self._createToolBar()
        
        app.aboutToQuit.connect(self.onExitButtonClick)

        acceptGUICommand("CONN")

    # This function builds the toolbar with its associated buttons and possible actions to invoke.
    def _createToolBar(self):

        # Creates a QToolBar object to attach actions to
        tools = QToolBar()

	# Creates a button on the toolbar for a home menu function
        tools.addAction("Home", self.onHomeButtonClick)

        # Creates a button on the toolbar for a Send File action 
        tools.addAction("Send File", self.onSendButtonClick)

        # Creates a button on the toolbar for a Receive File action 
        tools.addAction("Receive File", self.onReceiveButtonClick)

        # Creates a button on the toolbar for to trigger the exit function, closing the window
        tools.addAction("Exit", self.onExitButtonClick)

        # Adds the toolbar to the application window
        self.addToolBar(tools)

    """
        Function defines app behavior when the home button on the toolbar menu
        is clicked
    """
    def onHomeButtonClick(self):
        # Set up the layout
        layout = QVBoxLayout()

        # Check if the user is authenticated
        if self.is_authenticated:
            # If the user is authenticated, display a label welcoming the user to the app
            widget = QLabel("Welcome to the app!")
            layout.addWidget(widget)
        else:
            # If the user is not authenticated, display a button prompting the user to log in
            button = QPushButton("Log In")
            button.clicked.connect(self.authentication_function)
            layout.addWidget(button)
        # Set up a widget to hold the layout and assign it to the central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    """
        This function defines the behavior of the app when the Send File button is clicked
    """
    def onSendButtonClick(self):

        # Check if the user is authenticated
        if self.is_authenticated:
            # If the user is authenticated, display the file selection window
            dialog = QFileDialog()
            successful = dialog.exec()
            # If the user selects a file, send it to the server
            if(successful):
                print(dialog.selectedFiles()[0])
                # TODO implement functionality to interact with the server here., this is where the file
                # will be sent to the server
                acceptGUICommand("SEND", dialog.selectedFiles()[0])
                self.setCentralWidget(ReceiveFileWidget())
            # If the user closes the window or cancels, abort
            else:
                print("Aborted.")
        else:
            # If the user is not authenticated, attempt to authenticate them
            dlg = AuthenticationDialog(self)
            # If the authentication is successful, let the app know it has been authenticated
            if dlg.exec():
                self.is_authenticated = True
                self.log_in_button.setParent(None) # Set the home button's parent to none to remove it

                # Open the file selection dialog menu
                dialog = QFileDialog() 
                successful = dialog.exec()
                # If the user selects a file, send it to the server
                if(successful):
                    # TODO implement functionality to interact with the server here., this is where the file
                    # will be sent to the server
                    acceptGUICommand("SEND", dialog.selectedFiles()[0])
                    self.setCentralWidget(ReceiveFileWidget())
                # If the user closes the window or cancels, abort
                else:
                    print("Aborted.")
            # If the user fails to authenticate, exit the window
            else:
                print("Failed!")

    def onExitButtonClick(self):
        acceptGUICommand("EXIT")
        self.close()

    """
        This function defines the behavior of the app when the Receive File button is clicked
    """
    def onReceiveButtonClick(self):
        # If the user is authenticated, diaplay the Receive File Widget
        if self.is_authenticated:
            self.setCentralWidget(ReceiveFileWidget())
        # Otherwise, attempt to authenticate them
        else:
            dlg = AuthenticationDialog(self)
            # If the authentication succeeds, let the app know of the success and display the Receive File Widget
            if dlg.exec():
                self.is_authenticated = True
                self.log_in_button.setParent(None)
                self.setCentralWidget(ReceiveFileWidget())
            # Otherwise, exit the window
            else:
                print("Failed!")

    """
        Function to authenticate the user from the home widget
    """
    def authentication_function(self):
        dlg = AuthenticationDialog(self)
        # If authentication succeeds, let the app know of the success and remove the login button
        if dlg.exec():
            self.is_authenticated = True
            self.setCentralWidget(QLabel("LOGIN SUCCESSFUL"))
        # Otherwise, exit the window
        else:
            self.is_authenticated = False

"""
    Class to support the functionality to select a file and send
    it to the server
"""
class ReceiveFileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the layout format
        self.layout = QVBoxLayout()

        # Create a button to request a file
        button = QPushButton("Request File")
        button.clicked.connect(self.request_file)
        self.layout.addWidget(button)
        
        # Create a label to indicate the selected file
        self.selected_label = QLabel("Select a File:")
        self.layout.addWidget(self.selected_label)

        # Create a list widget to hold the retrieved file names from the server
        widget = QListWidget()

        # TODO Server interaction here... populate this with server
        # filesystem options
        file_list = acceptGUICommand("LIST")
        file_list.remove(file_list[len(file_list)-1])
        widget.addItems(file_list)

        # When the selected item changes, update the label
        widget.currentItemChanged.connect(self.index_changed)

        # Add the widget to the layout
        self.layout.addWidget(widget)

        # Set the layout
        self.setLayout(self.layout)

    """
        Function to update the selected file label on the widget
    """
    def index_changed(self, i):
        self.selected_label.setText(i.text())

    """
        Server interaction here to pull the requested file down from
        the server
    """
    def request_file(self):
        # If the label has been changed from the default, perform the action
        if self.selected_label.text() != "Select a File:":
            print(self.selected_label.text())
            acceptGUICommand("RECV", self.selected_label.text())
            window.setCentralWidget(ReceiveFileWidget())



"""
    Class to support the the authentication window for the
    application and its functionality of connecting to the server
"""
class AuthenticationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Instantiate window title and layout type
        self.setWindowTitle("Authentication Dialog")
        self.layout = QVBoxLayout()

        # Username field initialization
        self.layout.addWidget(QLabel("Username:"))
        self.user_name_input = QLineEdit()
        self.layout.addWidget(self.user_name_input)

        # Password field initialization
        self.layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_input)

        # Submit button initialization
        button = QPushButton("Authenticate")
        button.clicked.connect(self.attempt_authentication)
        self.layout.addWidget(button)

        # Layout construction
        self.setLayout(self.layout)
        
    """ 
        Functionality to interact with the server here, this is
        where the client attempts to authenticate with the server
    """
    def attempt_authentication(self):
        # User input values are accessed through self.<INPUT_TYPE>.text()
        if acceptGUICommand("AUTH", [self.user_name_input.text(), self.password_input.text()]):
            self.accept()
        else:
            self.reject()


# This block of code runs the app
if __name__ == "__main__":

    # Create a QApplication object to hold our window
    app = QApplication([])

    # Initialize a Window object from the above class
    window = Window()

    # Display the window in the application
    window.show()

    # Exit the program when the app is closed
    sys.exit(app.exec())
