# Installation Instructions

We recommend that end-users run Basement Renovator directly from the source code.

* [Installation for Beginners using Chocolatey](#installation-for-beginners-using-chocolatey)
* [Installation for Advanced Users](#installation-for-advanced-users)

<br />

## Installation for Beginners Using Chocolatey

If you are not using Windows 10, see the [section below](#installation-for-advanced-users).

- Open a [Command Prompt as an administrator](https://www.howtogeek.com/194041/how-to-open-the-command-prompt-as-administrator-in-windows-8.1/). (Read the link if you don't know how.)
- Install [Chocolatey](https://chocolatey.org/) by copy-pasting the following command. (Skip this step if you have already have Chocolatey installed on your computer.)
  - `@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"`
- Install [Git](https://git-scm.com/) by copy-pasting the following command. (Skip this step if you have already have Git installed on your computer.)
  - `choco install git -y`
- Install [Python 3](https://www.python.org/) by copy-pasting the following command. (Skip this step if you have already have Python 3 installed on your computer.)
  - `choco install python3 -y`
- Install the [Microsoft Visual C++ Build Tools 2015](https://chocolatey.org/packages/microsoft-visual-cpp-build-tools) by copy-pasting the following command. (This is needed in order to install the Python dependencies. Skip this step if you have already have it installed on your computer.)
  - `choco install microsoft-visual-cpp-build-tools -y`
- Clone the Basement Renoavtor repository:
  - `cd %userprofile%\Documents` <br />
  (this changes the directory to your Documents directory; if you want the Basement Renoavtor repository to live somewhere else, then change the command accordingly)
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

## Installation for Advanced Users

- Download a copy of the source code, either by cloning the repository or by clicking [here](https://github.com/Tempus/Basement-Renovator/archive/master.zip).
- Install [Python 3](https://www.python.org/) if you do not have it installed already. (If you are on Windows, installing with [Chocolately](https://chocolatey.org/) is recommended, but you can also manually download the MSI file and click "next" through the install wizard yourself if you want.)
- Open a command prompt / terminal and run the following in the Basement Renovator directory to install the Python dependencies:
  - `pip install -r requirements.txt` <br />
    (if you are on Windows, you might also need to install Microsoft Visual C++ Build Tools 2015 in order for the dependencies to compile, if you do not have it installed already)
- Run the following in the Basement Renovator directory to start the program:
  - `python BasementRenovator.py` <br />
  (or you can just double click on the "BasementRenovator.py" file)
