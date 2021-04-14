# Run the Latest Release

The latest release can be found in the [releases tab](https://github.com/Tempus/Basement-Renovator/releases). This is most likely out of date, so running from source is recommended.

# Running from Source

Because Basement Renovator's build schedule is irregular, it's recommended to run it directly from the source code.

## Chocolatey

Running Basement Renovator from source requires Python to be installed, as well as some other dependencies. In order to install everything, we recommend using [Chocolatey](https://chocolatey.org/), which is a package manager for Windows. It is the defacto way to install software without having to manually click anything.

If you are not using Windows 10, see the [section below](#python).

- First, manually download and install the latest version of [Python](https://www.python.org/downloads/) from the official website.
  - Make sure that you check the box to add Python to your PATH. Otherwise, the below `python` commands will not work.
  - Do not install Python from Chocolatey, as it results in bugs with not being able to invoke command-line Python applications.
- Open a [Command Prompt as an administrator](https://www.howtogeek.com/194041/how-to-open-the-command-prompt-as-administrator-in-windows-8.1/). (Read the link if you don't know how.)
- Install [Chocolatey](https://chocolatey.org/) by copy-pasting the following command. (Skip this step if you have already have Chocolatey installed on your computer.)
  - `@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"`
- Install [Git](https://git-scm.com/) by copy-pasting the following command. (Skip this step if you have already have Git installed on your computer.)
  - `choco install git -y`
- Install the [Microsoft Visual C++ Build Tools 2015](https://chocolatey.org/packages/microsoft-visual-cpp-build-tools) by copy-pasting the following command. (This is needed in order to install the Python dependencies. Skip this step if you have already have it installed on your computer.)
  - `choco install microsoft-visual-cpp-build-tools -y`
- Change the working directory to your Documents directory:
  - `cd %userprofile%\Documents` <br />
  (if you want the Basement Renovator repository to live somewhere else, then change the command accordingly)
- Clone the Basement Renovator repository:
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

## Minimal

This section has installation instructions for only installing what is explicitly needed. If you encounter errors, try following the Chocolatey instructions above.

- First, manually download and install the latest version of [Python](https://www.python.org/downloads/) from the official website.
  - Make sure that you check the box to add Python to your PATH. Otherwise, the below `python` commands will not work.
- Download a copy of the source code, either by cloning the repository or by clicking [here](https://github.com/Tempus/Basement-Renovator/archive/master.zip).
- Double-click the `BR.bat` file in the root of the install folder.
  - This will print your Python version, run `pip` to install BR's dependencies, and and then run "BasementRenovator.py".
  - After the program is closed or crashes, the console window will remain open so that you can read the error logs.
