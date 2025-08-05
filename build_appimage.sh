#!/bin/bash

# Amadinda Trainer AppImage Builder
# This script builds the Amadinda Trainer as an AppImage

echo "Building Amadinda Trainer AppImage..."

# Activate virtual environment
source amadinda_env/bin/activate

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist build AmadindaTrainer.AppDir

# Build executable with PyInstaller
echo "Building executable with PyInstaller..."
pyinstaller --onefile --windowed --add-data "samples:samples" --add-data "config.py:." --name "AmadindaTrainer" amadinda_trainer.py

# Create AppDir structure
echo "Creating AppDir structure..."
mkdir -p AmadindaTrainer.AppDir/usr/bin
mkdir -p AmadindaTrainer.AppDir/usr/share/icons/hicolor/256x256/apps

# Copy executable
cp dist/AmadindaTrainer AmadindaTrainer.AppDir/usr/bin/

# Create desktop file
cat > AmadindaTrainer.AppDir/AmadindaTrainer.desktop << EOF
[Desktop Entry]
Name=Amadinda Trainer
Comment=Educational tool for learning Ugandan amadinda xylophone patterns
Exec=AmadindaTrainer
Icon=amadinda-trainer
Type=Application
Categories=Education;
Keywords=music;education;xylophone;amadinda;uganda;african;
StartupWMClass=AmadindaTrainer
EOF

# Create AppRun script
cat > AmadindaTrainer.AppDir/AppRun << EOF
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export PATH="\${HERE}"/usr/bin/:"\${PATH}"
export LD_LIBRARY_PATH="\${HERE}"/usr/lib/:"\${LD_LIBRARY_PATH}"
exec "\${HERE}"/usr/bin/AmadindaTrainer "\$@"
EOF

chmod +x AmadindaTrainer.AppDir/AppRun

# Copy icon
cp docs/Paomedia_small-n-flat_mixer.svg AmadindaTrainer.AppDir/usr/share/icons/hicolor/256x256/apps/amadinda-trainer.svg
convert docs/Paomedia_small-n-flat_mixer.svg AmadindaTrainer.AppDir/amadinda-trainer.png

# Create AppImage
echo "Creating AppImage..."
./appimagetool AmadindaTrainer.AppDir AmadindaTrainer-x86_64.AppImage

echo "AppImage created successfully: AmadindaTrainer-x86_64.AppImage"
echo "Size: $(ls -lh AmadindaTrainer-x86_64.AppImage | awk '{print $5}')" 