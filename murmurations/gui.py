from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtGui import QColor

"""
Qt doesn't like being put on a thread so this will have to run as a separate process and talk over a server
"""
# TODO server stuff


class GuiForm(QtCore.QObject):
    def __init__(self):
        super(GuiForm, self).__init__()
        self.ui = None
        self.ui = uic.loadUi("GUIsettings.ui", self.ui)

        # TODO we're going to have to update all sliders every time we change
        self.swarm_in_focus = 0

        # TODO set

        # num boids and attractors
        # print(*dir(self.ui.num_boids_spin))
        self.ui.num_boids_spin.editingFinished.connect(
            lambda: self.spin_box_changed(self.ui.num_boids_spin, "num_boids")
        )
        self.ui.num_atts_spin.editingFinished.connect(
            lambda: self.spin_box_changed(self.ui.num_atts_spin, "num_atts")
        )

        # TODO actions & buttons and stuff
        # print(dir(self.ui.open_file_dialog))
        self.ui.open_file_dialog.clicked.connect(self.browse_files)

        # TODO get actual colour of swarm
        col = QColor(0, 0, 0)
        self.ui.colour_button.clicked.connect(self.change_colour)
        self.set_colour(self.ui.colour_frame, col)

        self.ui.show()

    def spin_box_changed(self, sb, command):
        self.send_message("{}: {}".format(command, sb.value()))

    def change_swarm_focus(self, swarm):
        # TODO read in all the values and set the sliders appropriately
        raise NotImplementedError

    def set_colour(self, frame, col):
        frame.setStyleSheet("QWidget { background-color: %s }" % col.name())

    def change_colour(self):
        col = QtWidgets.QColorDialog.getColor()
        if col.isValid():
            self.set_colour(self.ui.colour_frame, col)
            self.send_message("{}: {}".format("colour", col))

    def browse_files(self):
        # TODO restrict to JSON files (setNameFilter??)
        fltr = "JSON (*.json)"
        fname = QtWidgets.QFileDialog.getOpenFileName(
            self.ui, "Open file", "./", filter=fltr
        )
        if fname[0]:
            self.ui.display_preset_name.setText(fname[0].split("/")[-1])

    def send_message(self, message):
        # TODO send over server or something
        # Must check on other end if the message actually changes anything
        # In case of duplicates (esp. spin boxes)
        print(message)


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    # Form = QtWidgets.QWidget()
    ui = GuiForm()
    # ui.setupUi(Form)
    # Form.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
