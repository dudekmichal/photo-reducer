#!/usr/bin/env python

import os
import io
import math
from sys import argv, platform, stderr
import glob
from PIL import Image, ExifTags

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from gui_main_window import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Class containing all methods using elements of the graphic interface.
    """
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.button_get_dir_path.clicked.connect(self.browse_directories)
        self.button_start_reducing.clicked.connect(self.start_converting)
        self.progressbar_reducing.setValue(0)
        if platform == "win32":
            self.formats = ["jpg", "jpeg", "png"]
        else:
            self.formats = ["jpg", "JPG", "jpeg", "JPEG", "png", "PNG"]

    def browse_directories(self):
        """
        Select a directory containing photos.
        """
        dirname = str(QFileDialog.getExistingDirectory(self, "Select directory"))
        self.line_edit_dir_path.setText(dirname)
        self.get_number_of_photos_in_specified_dir()

    def get_number_of_photos_in_specified_dir(self):
        """
        Get number of photos in specified directory.
        """
        photos_count = 0
        path = self.line_edit_dir_path.text()
        for f in self.formats:
            photos_count += len(glob.glob1(path,"*.{}".format(f)))
        self.progressbar_reducing.setMaximum(photos_count)
        self.progressbar_reducing.setValue(0)
        self.label_photos_count.setText(str(photos_count))

    def update_progressbar(self):
        """
        Update a progress bar.
        """
        self.progressbar_reducing.setValue(self.progressbar_reducing.value() + 1)
        QApplication.processEvents()

    def close_app(self):
        """
        Close app.
        """
        app.quit()

    def start_converting(self):
        """
        Start converting photos to specified size.
        """
        self.progressbar_reducing.setValue(0)
        path = self.line_edit_dir_path.text()
        dest_path = os.path.join(path, r"reduced_photos")
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        max_size =  int(self.max_size_value_MB.value() * 1048576)

        for image_format in self.formats:
            for filename in glob.glob('{}/*.{}'.format(path, image_format)):
                self.label_converting_file.setText(
                    "Converting file: {}...".format(filename))
                self.jpeg_save_with_target_size(
                    filename, max_size, dest_path)
                self.update_progressbar()
        self.label_converting_file.setText("Done!")

    def jpeg_save_with_target_size(self, filename, target, dest_path):
        """
        Save the image as JPEG with the given name at best quality that makes
        less than "target" bytes.
        """
        basename = os.path.basename(filename)
        extension = os.path.splitext(filename)[1].lstrip('.')
        img = Image.open(filename)
        try:
            exif=dict((ExifTags.TAGS[k], v) for k, v in img._getexif().items()
                if k in ExifTags.TAGS)
            if exif['Orientation'] == 3:
                img=img.rotate(180, expand=True)
            elif exif['Orientation'] == 6:
                img=img.rotate(270, expand=True)
            elif exif['Orientation'] == 8:
                img=img.rotate(90, expand=True)
        except AttributeError:
            print("Cannot read metadata for the photo.")

        # Min and Max quality
        quality_min, quality_max = 1, 96

        # Highest acceptable quality found
        quality_best_acceptable = -1

        while quality_min <= quality_max:
            quality_tmp = math.floor((quality_min + quality_max) / 2)

            # Encode into memory and get size
            buffer = io.BytesIO()
            img.save(buffer, format="jpeg", quality=quality_tmp)
            size_bytes = buffer.getbuffer().nbytes

            if size_bytes <= target:
                quality_best_acceptable = quality_tmp
                quality_min = quality_tmp + 1
            elif size_bytes > target:
                quality_max = quality_tmp - 1

        # Write to disk at the defined quality
        if quality_best_acceptable > -1:
            print("Saving to: {}".format(os.path.join(dest_path, basename)))
            dest_file = os.path.join(dest_path, basename)
            img.save(
                dest_file, format="jpeg", quality=quality_best_acceptable)
        else:
            print("ERROR: No acceptable quality factor found.", file=stderr)

if __name__ == '__main__':
    app = QApplication(argv)
    form = MainWindow()
    form.show()
    app.exec_()
