# Sherloc 
### A.K.A. Software to Help with Evidence Retrieval and Log Online Cyberabuse

Sherloc is a tool to support computer security clinics. It is meant to be run by a tech clinic consultant, allowing the consultant to enter findings and investigations. Then, Sherloc enables the consultant to create an evidentiary document synthesizing the consultation.

Sherloc is built on [ISDI](https://github.com/stopipv/isdi), which checks Android or iOS devices for spyware.

## Installing Sherloc :computer:

Right now, Sherloc only natively supports **macOS and Linux**. If you are using a Windows device, you can use the Windows Subsystem for Linux 2
(WSL2), which can be installed by following [these instructions](https://docs.microsoft.com/en-us/windows/wsl/wsl2-install). After this,
follow the remaining instructions as a Linux user would, cloning/running 
Sherloc inside the Linux container of your choice. 

### Python dependencies
- You will need Python 3.6 or higher (check by running `python3` in your
Terminal and see what happens). On macOS, you can get this by running the
following commands in your Terminal application:

```bash
# Installs developer tools
xcode-select --install 

# Installs Brew (a software package manager)
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# Installs Python3.10
brew install python@3.10
```

### WeasyPrint requirement
The updated code uses WeasyPrint for pdf rendering and requires the below installations:

macOS (Intel + Apple Silicon):

brew install pango libffi cairo gdk-pixbuf

Linux (Ubuntu/Debian):
sudo apt install libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi8


### Operating system dependencies

#### Generic
* [adb](https://developer.android.com/studio/releases/platform-tools.html)
* expect
* ideviceinstaller

#### macOS
On macOS you can quickly install project dependencies with Homebrew by running `brew bundle`.

You can also fulfill the requirements by doing:
```bash
brew install --cask android-platform-tools
brew install expect ideviceinstaller exiftool
```

#### Debian family

```
sudo apt install adb expect libimobiledevice-utils ideviceinstaller ifuse
```

#### Windows Subsystem Linux (v2)
Installing **adb** is not so straightforward in WSL2, and
it won't work straightaway. You have to ensure having the *same* version of adb
*both* in WSL2 and in normal Windows (with `adb version`), then you will need to
start the adb process first in Windows, then in WSL2 (with for example `adb
devices`).

# Running Sherloc

After Sherloc is installed, run the following command in the terminal (in
the top-level directory of this repository):

```bash
cd sherloc
./sherloc.sh
```

There is an optional `--install` flag that installs requirements from `requirements.txt`. However, even without this flag, the script will notice if sherloc fails and install requirements anyway.

Sherloc is run in sudo by default, which is required to take screenshots on iPhones using `pymobiledevice3`. If you do not want to run Sherloc with sudo, please use the `--nosudo` flag when running `./sherloc`. 

Sherloc should open `http://localhost:6200` in the browser.

## Requirements for taking screenshots with iOS devices

iOS devices have two requirements if you want to take screenshots. 

1. Developer mode must be on (instructions below). 
2. Sherloc must be run in `sudo`, which is the default when using `./sherloc.sh`.

To turn on developer mode:
1. Plug in the client’s phone.
2. Open XCode and start the OpenHaystack project.
3. Go to Product -> Destination -> Manage Run Destinations
4. Choose the client’s phone as the run location and hit Run. If it says Developer Mode must be opted into, hit cancel. Then enable Developer Mode on the phone in Settings > Privacy & Security > Developer Mode.
5. Restart the phone.

Please see this article for more details on how to turn on developer mode using XCode: https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device.

## Debugging tips 
If you encounter errors, please file a [GitHub issue](../../issues/) with the server error output. 
Pull requests are welcome. 

#### Cast iOS Screens or Mirror Android Screens 
It is possible to view your
device screen(s) in real time on the macOS computer in a new window. This may
be useful to have while you are running the scan (and especially if you use the
privacy checkup feature), as it will be easy for you to see the mobile device
screen(s) in real time on the Mac side-by-side with the scanner.

**How to do it:** 
You can mirror Android device screens in a new window using
[scrcpy](https://github.com/Genymobile/scrcpy), and cast iOS device screens on
macOS with QuickTime 10 (launch it and click File --> New Movie Recording -->
(on dropdown by red button) the iPhone/iPad name).

## Downloaded data ## 
The data downloaded and stored in the study are the
following.  1. A `sqlite` database containing the feedback and actions taken by
the user.  2. `phone_dump/` folder will have dump of some services in the
phone.  (For Android I have figured out what are these, for iOS I don't know
how to get those information.)

##### Android 
The services that we can dump safely using `dumpsys` are the
following.
* Application static details: `package` Sensor and configuration info:
* `location`, `media.camera`, `netpolicy`, `mount` Resource information:
* `cpuinfo`, `dbinfo`, `meminfo` Resource consumption: `procstats`,
* `batterystats`, `netstats`, `usagestats` App running information: `activity`,
* `appops`

See details about the services in [notes.md](notes.md)

##### iOS 
Only the `appIds`, and their names. Also, I got "permissions" granted
to the application. I don't know how to get install date, resource usage, etc.
(Any help will be greatly welcomed.)

##### Post PDF generation
Everything that is required for the Post PDF generation is in the post_pdf directory and below instructions assume that the user in that directory.

Save the PDF in the sherloc_output subfolder.

After saving it, generate a version of PDF with aruco markers. This will rescale the PDF and put aruco markers on the corners. These markers help in aligning the PDF images with the camera images and scale them for comparision.

To generate a version of PDF with aruco markers, go to the code folder and run the generate_aruco_markers.sh script.

Make sure the script is executable 
```bash
chmod +x add_aruco_markers.sh
```
and run it 
```bash
./add_aruco_markers.sh
```
This installs all the requirements to generate the PDF with aruco markers and places <report>_marked.pdf in the sherloc_output folder.

Now, print the PDF and take pictures of it with camera/scan and upload the images in camera_images_input folder. Make sure there are numbered correctly in tune with PDF.

Now, run 
```bash
./google_ocr_align.sh 
```
This will essentially create images of the PDF and store them in clean_pdf_rendered_images folder and then uses aruco markers to rescale and align images from camera_images_input folder into camera_rendered_aligned_images.

It then compares the images in camera_rendered_aligned_images with the images in clean_pdf_rendered_images according to their names and then places the final annoatated image highlighting differences in annotated_difference_images. 

The debug_purpose folder has CSV and text output along with the diff output for debug purposes.

We store the google_ocr_key in google_OCR_key folder. This is needed to call google vision API that is used for OCR.
