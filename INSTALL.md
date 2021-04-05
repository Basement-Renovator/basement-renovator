# Run the Latest Release

The latest release can be found in the [releases tab](https://github.com/Tempus/Basement-Renovator/releases). This is most likely out of date, so running from source is recommended.

# Running from Source

Because Basement Renovator's build schedule is irregular, it's recommended to run it directly from the source code

## Chocolatey

The advantage of Chocolatey is that while you have to install another piece of software your installation will be simple to keep up to date in the future. Setup can also be less errorprone.

If you are not using Windows 10, see the [section below](#python).

- Open a [Command Prompt as an administrator](https://www.howtogeek.com/194041/how-to-open-the-command-prompt-as-administrator-in-windows-8.1/). (Read the link if you don't know how.)
- Install [Chocolatey](https://chocolatey.org/) by copy-pasting the following command. (Skip this step if you have already have Chocolatey installed on your computer.)
  - `@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"`
- Install [Git](https://git-scm.com/) by copy-pasting the following command. (Skip this step if you have already have Git installed on your computer.)
  - `choco install git -y`
- Install [Python 3](https://www.python.org/) by copy-pasting the following command. (Skip this step if you have already have Python 3 installed on your computer.)
  - `choco install python3 -y`
- Install the [Microsoft Visual C++ Build Tools 2015](https://chocolatey.org/packages/microsoft-visual-cpp-build-tools) by copy-pasting the following command. (This is needed in order to install the Python dependencies. Skip this step if you have already have it installed on your computer.)
  - `choco install microsoft-visual-cpp-build-tools -y`
- Clone the Basement Renovator repository:
  - `cd %userprofile%\Documents` <br />
  (this changes the directory to your Documents directory; if you want the Basement Renovator repository to live somewhere else, then change the command accordingly)
  - `refreshenv`
  - `git clone https://github.com/Tempus/Basement-Renovator.git`
- Go into the cloned directory:
  - `cd Basement-Renovator`
- Install the Python dependencies:
  - `pip install -r requirements.txt`
- Run it:
  - `python BasementRenovator.py`
- Wait up to 30 seconds or so for Basement Renovator to open. If it opens, you are done. In the future, you can just double click on the "BasementRenovator.py" file to open the program.
- Otherwise, read the error messages in the command prompt and try to figure out what went wrong.

<br />

## Python

This installation only installs what is explicitly needed to run Basement Renovator from source.

- Download a copy of the source code, either by cloning the repository or by clicking [here](https://github.com/Tempus/Basement-Renovator/archive/master.zip).
- Install Python 3 from the [Python website](https://www.python.org/downloads/)
  - If you are manually installing it, then make sure to check the box to add Python to your PATH. Otherwise, the next steps will complain about the `python` command not existing
  - Double-click `BR.bat` in the root of the install folder
    - This will print your Python version, run `pip` to install BR's dependencies, and and then run BasementRenovator.py
    - After BR is closed or crashes, the console window will remain open to read the error logs
