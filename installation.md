## Run the Latest Release

The latest release can be found in the [releases tab](https://github.com/Tempus/Basement-Renovator/releases). This is most likely out of date, so running from source is recommended.

## Running from Source

Because Basement Renovator's build schedule is irregular, it's recommended to run it directly from the source code

## Chocolatey

If you are not using Windows 10, see the [section below](#python).

- Open a [Command Prompt as an administrator](https://www.howtogeek.com/194041/how-to-open-the-command-prompt-as-administrator-in-windows-8.1/).
- Install [Chocolatey](https://chocolatey.org/) by copy-pasting the following command:
  - `@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"`
- Install [Git](https://git-scm.com/), [Python 3](https://www.python.org/), and the [Microsoft Visual C++ Build Tools 2015](https://chocolatey.org/packages/microsoft-visual-cpp-build-tools) by copy-pasting the following commands:
  - `choco install git python3 choco microsoft-visual-cpp-build-tools -y`
  - `refreshenv`
- Clone the repository:
  - `cd %userprofile%\Documents` <br />
  (this changes the directory to your Documents directory; if you want the repository to live somewhere else, then change the command accordingly)
  - `git clone https://github.com/Tempus/Basement-Renovator.git`
- Go into the cloned directory:
  - `cd Basement-Renovator`
- Install the Python dependencies:
  - `pip install -r requirements.txt`
- Run it:
  - `python BasementRenovator.py`
- Wait up to 30 seconds or so for Basement Renovator to open. If it opens, you are done. In the future, you can just double click on the "BasementRenovator.py" file to open the program.
- Otherwise, read the error messages in the command prompt and try to figure out what went wrong.

## Python

- Download a copy of the source code, either by cloning the repository or by clicking [here](https://github.com/Tempus/Basement-Renovator/archive/master.zip).
- Install Python 3 from the [Python website](https://www.python.org/downloads/).
  - If you are manually installing it, then make sure to check the box to add Python to your PATH. Otherwise, the next steps will complain about the `python` command not existing.
  - Installing Python 3 should also install `pip`, the Python package manager.
- Shift + Right Click in the Basement Renovator folder and click Open Powershell.
- Copy-paste `pip install -r requirements.txt` and press enter to install the Python dependencies. (this runs the command)
- Run `python ./BasementRenovator.py`, or double click the "BasementRenovator.py" script.
  - Errors will only stay on screen if you run from Powershell