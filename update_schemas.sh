#!/bin/bash
# This script is used to update the schemas for the Microsoft Sentinel data connectors.
# It will clone the necessary repositories, check out the relevant directories, and run a Python script to get the latest schemas.
# It is assumed that the script is run from the root directory of the repository.
if [ ! -d "src" ]; then
    echo "This script must be run from the root directory of the repository."
    exit 1
fi
if [ ! -d "azure-reference-others" ]; then
    git clone --depth=1 https://github.com/MicrosoftDocs/azure-reference-other ; cd azure-reference-other ; git checkout bea53845fef94ad4f1887d306e6618a34efefc01 ; cd ..
fi
# Check out the relevant directories for Defender XDR
if [ ! -d "defender-docs" ];  then
    git clone --filter=blob:none --sparse --depth=1 https://github.com/MicrosoftDocs/defender-docs ; cd defender-docs ; git sparse-checkout set defender-xdr includes ; cd ..
fi else
    cd defender-docs ; git sparse-checkout set defender-xdr ; cd ..
fi
# Get the latest schemas
python3 get_schemas.py > environments.json
