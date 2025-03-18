# image-organizer
Quickly Organizes Image based on filename or metadata

This project includes a script to organize images based on metadata extracted from the image files. It allows for efficient sorting and categorization of images in a designated folder.

## Overview

The image organization script scans a specified source folder for images and moves them into categorized folders based on keywords. It can also extract metadata prompts from image files to determine the category in which the image should be placed.

## Scripts

### organize_images.py

- **Functionality**: 
  - Scans a source folder for image files.
  - Moves images into newly created folders based on specific keywords or extracted metadata.
- **Keywords**: 
  - You can customize the list of keywords to categorize images. Currently, the script includes a placeholder for a keyword ("cirno").

### Metadata Extraction

- The script is capable of extracting the "prompts" metadata field from image files using the `exifread` library. This metadata can then be used to categorize images if no specific keyword match occurs.

## Requirements

To run this script, you'll need the following Python libraries:

```bash
pip install pillow exifread
```

## Configuration

Make sure to adjust the following constants in the script before running:

- **SOURCE_FOLDER**: Change this to your directory containing the images you want to organize.
- **DESTINATION_FOLDER**: Change this to your desired directory for sorted images.
- **KEYWORDS**: Customize this list with the keywords you want to use for categorizing images based on filenames.

## Usage

To execute the script, run the following command in your terminal:

```bash
python organize_images.py
```

This will start the organization process, moving images from the source folder to their appropriate categorized folders in the destination directory.
