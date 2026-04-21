# Build `.exe`

The project can now be packed into a ready-to-run Windows distribution with PyInstaller.

## First-time setup

```powershell
python -m pip install -r requirements-build.txt
```

## Build

```powershell
.\build_exe.ps1
```

The ready executable will be created here:

```text
dist\StarClassifier\StarClassifier.exe
```

## Runtime behavior of the packaged app

- The `dist\StarClassifier\` folder contains the executable plus bundled runtime files.
- On first launch, the app copies the editable knowledge base and the trained ML model into the user's local app data folder.
- By default this folder is:

```text
%LOCALAPPDATA%\StarClassifier
```

- This means the user can launch the `.exe` without installing Python.
- Changes to the knowledge base and retrained models persist between launches.
- If needed, the storage folder can be overridden with the `STAR_CLASSIFIER_HOME` environment variable.
