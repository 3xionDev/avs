AVS (ASCII Video Stream) is a suite of tools for playing videos in your terminal
***
Status:
- In development
- Early access (beta)
- Contributions open
***
## What is AVS?
In short, the AVS suite is composed of three things: the [[AVS format]], the [[AVS encoder]], and the [[AVS decoder]]. The purpose of the AVS project is to provide a user-friendly and simple solution to people looking to include simple animations in their CLI tools.

## Installation
The full AVS suite can be installed either from source or from your Linux distribution's package package manager (if it can be found in your repository).
### Arch Linux
`avsutil` can be found on the AUR (Arch User Repository). Install it with your preferred AUR helper:
```
yay -S avsutil
```
or, if you use paru,
```
paru -S avsutil
```
You can also manually build the PKGBUILD, if you'd like.
### Fedora/RHEL/CentOS
`avsutil` is found on the Fedora Copr repository. Install it with `dnf` like so:
```
sudo dnf copr enable 3xiondev/avsutil
sudo dnf install avsutil
```

### Other distributions
Prebuilt binaries are found on the releases page. You may also run the script directly. For those that prefer the latter, the dependencies are:
- NumPy
- ffmpeg-python
- opencv-python
- Pillow
- tqdm

Create a virtual environment and install the dependencies with:
```
pip install numpy ffmpeg-python opencv-python pillow tqdm
```

## Contributing
If you'd like to contribute to anything in the AVS suite, please open a pull request AND an issue. If you only open a pull request, chances are that I will not see it for a while. For a quick response and review, an issue is your best option.

## License
AVS and its related software are licensed under the GNU General Public License Version 3 (GPLv3). Under this license, the code is to remain open source, and anyone is free to use, copy, or modify the code. Derivatives of this software must also be licensed under GPLv3. Closed-source derivatives of this software or its code are forbidden. If any violation of the terms of GPLv3 (found here: [[LICENSE]]) are found in this software or any of its derivatives, they are to be remedied within 30 days of detection, otherwise the license will be permanently revoked.