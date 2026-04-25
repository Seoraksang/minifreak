# Phase 5: MiniFreak V DLL Binary Analysis

**Date:** 2026-04-24  
**File:** `MiniFreak V.dll` (30.3 MB, PE32+ x86-64)  
**Source:** Arturia MiniFreak V desktop software (extracted from installer)

---

## 1. DLL Overview

| Property | Value |
|----------|-------|
| Format | PE32+ (64-bit DLL) |
| Architecture | AMD64 (x86-64) |
| Image Base | 0x180000000 |
| Entry Point | 0x120a1e4 |
| Export Name | `minifreakv_vst3.vst3` (324 exports) |
| Build System | Jenkins (`C:\jenkins\root\workspace\VC\release\minifreakv\`) |
| Framework | JUCE + VST3 7.7.5 + Arturia internal libraries |

### PE Sections

| Section | VirtAddr | VirtSize | RawSize | Description |
|---------|----------|----------|---------|-------------|
| `.text` | 0x1000 | 0x133250c | 0x1332600 | Main code (20.3 MB) |
| `IPPCODE` | 0x1334000 | 0x9cf3d | 0x9d000 | Intel IPP DSP code (640 KB) |
| `.rdata` | 0x13d1000 | 0x692480 | 0x692600 | Read-only data (6.8 MB) |
| `.data` | 0x1a64000 | 0x131f10 | 0x10e200 | Initialized data |
| `.pdata` | 0x1b96000 | 0xc2040 | 0xc2200 | Exception handling |
| `IPPDATA` | 0x1c59000 | 0xac0 | 0xc00 | Intel IPP data |
| `_RDATA` | 0x1c5a000 | 0x24b10 | 0x24c00 | Additional rdata |
| `.rsrc` | 0x1c7f000 | 0x5c8 | 0x600 | Resources |
| `.reloc` | 0x1c80000 | 0x6993c | 0x69a00 | Relocations |

### DLL Imports (key)

- `WINMM.dll` — Windows Multimedia (MIDI API: midiIn*, midiOut*)
- `KERNEL32.dll`, `USER32.dll`, `GDI32.dll`, `SHELL32.dll` — Windows core
- `WS2_32.dll` — Winsock networking
- `WININET.dll` — HTTP (firmware update checks)
- `OPENGL32.dll` — GUI rendering
- `CRYPT32.dll` — Cryptography (ASC protection)
- `IPHLPAPI.DLL` — IP helper (network interface detection)

---

## 2. SysEx Message Templates & MIDI Communication

### 2.1 Arturia SysEx Header

**Header bytes:** `F0 00 20 6B`

Found **84 occurrences** of the `00 20 6B` byte pattern and **22 occurrences** of the full `F0 00 20 6B` sequence in the binary. These are embedded directly in x86-64 machine code as immediate values (MOV instructions), constructing SysEx messages at runtime.

### 2.2 SysEx Message Format

```
Byte 0:     F0          (SysEx Start)
Byte 1-3:   00 20 6B    (Arturia Manufacturer ID: 0x00 0x20 = DevID, 0x6B = Family)
Byte 4:     Device ID   (0x02 = MiniFreak specific, 0x7F = broadcast/any)
Byte 5:     Message Type
Byte 6:     Group/Category
Byte 7+:    Parameter data
Last byte:  F7          (SysEx End)
```

### 2.3 Identified SysEx Message Types (from code analysis)

| Offset | Template Bytes | Description |
|--------|---------------|-------------|
| 0x574157 | `F0 00 20 6B 02 02 03 ... F7` | RPN parameter request (dev=0x02, type=0x02, grp=0x03) |
| 0x5743bc | `F0 00 20 6B 02 02 03 ... F7` | RPN parameter set (same group, value follows) |
| 0x57448a | `F0 00 20 6B 02 02 03 ... F7` | RPN parameter (variant with bitmask ops) |
| 0x57464b | `F0 00 20 6B 7F 42 02 ... F7` | Broadcast request (dev=0x7F, type=0x42, grp=0x02) |
| 0x5748fc | `F0 00 20 6B 7F 42 02 ... F7` | Request variant with value byte |
| 0x574b80 | `F0 00 20 6B 02 08 03 ... F7` | Parameter (dev=0x02, type=0x08, grp=0x03) |
| 0x574fbc | `F0 00 20 6B 7F 42 02 10 ... F7` | Request with param ID 0x10 |
| 0x575567 | `F0 00 20 6B 7F 42 02 11 ... F7` | Request with param ID 0x11 |
| 0x575be2 | `F0 00 20 6B 7F 42 04 ... F7` | System group request (grp=0x04) |
| 0x575ffd | `F0 00 20 6B 7F 42 0A ... F7` | Extended/firmware group (grp=0x0A) |
| 0x576498 | `F0 00 20 6B 7F 42 0A ... F7` | Extended/firmware (variant) |
| 0x15cf7d8 | `F0 00 20 6B 7F 42 00 00 08 ...` | Data template in .rdata section |

### 2.4 SysEx Message Type Codes

| Type | Purpose |
|------|---------|
| `0x02` | Parameter Get/Set (targeted, dev=0x02) |
| `0x08` | Parameter (alternate channel) |
| `0x42` | Request/Query (broadcast, dev=0x7F) |

### 2.5 SysEx Group Codes

| Group | Purpose |
|-------|---------|
| `0x02` | Parameter group |
| `0x03` | RPN/NRPN parameters |
| `0x04` | System parameters |
| `0x0A` | Extended/Firmware parameters |

### 2.6 SysEx-Related Classes

- `Arturia::WrapperLib::SysexComponent` — SysEx UI component
- `Arturia::WrapperLib::SysexScreen` — SysEx display screen
- `Arturia::WrapperLib::SysexTabGroup` — SysEx tab management
- `Arturia::WrapperLib::SysexUIBuilder` — SysEx UI construction
- `Arturia::WrapperLib::SysexButton` — SysEx trigger button
- `Arturia::WrapperLib::KL3SysexButtonControlled` — KeyLab 3 SysEx button
- `Arturia::WrapperLib::OutputHWManager::BuildSysexBrowser` — SysEx browser

### 2.7 Key SysEx Strings

- `"Error: Unfinished SysEx: missing F7."` — Validates SysEx termination
- `"Ex: midi f0 ... f7 // sysex"` — Documentation/help text
- `"Import Sysex"` — UI for importing SysEx files
- `"The Sysex file could not be converted."` — Error message
- `"Receive Sysex Data : ignored"` — Inbound SysEx handling

---

## 3. Arturia "Collage" USB Protocol

### 3.1 Protocol Architecture

The DLL contains a complete **Protobuf-based communication protocol** called **"Collage"** (`Arturia::Collage` namespace). This is Arturia's custom USB communication framework used between the VST plugin and the hardware.

### 3.2 Communication Layers

| Component | Class | Purpose |
|-----------|-------|---------|
| USB Transport | `Arturia::Collage::CommUsb` | USB bulk transfer layer |
| TCP Transport | `Arturia::Collage::CommTcp` | TCP fallback/debug transport |
| Protocol | `Arturia::Collage::ProtocolProtobuf` | Protobuf serialization |
| Raw Protocol | `Arturia::Collage::ProtocolRaw` | Raw binary protocol |
| Channel | `Arturia::Collage::Channel` | Multiplexed communication channels |
| Command Manager | `Arturia::Collage::CollageCommandManager` | Command dispatch |
| Buffer Queue | `Arturia::Collage::BufferPriorityQueue` | Priority-buffered message queue |

### 3.3 Protobuf Message Types

The protocol defines these service domains:

#### Data Service (`Arturia.Collage.Protobuf.Data*`)
- `DataParameterGetRequest/Response` — Get parameter value
- `DataParameterSetRequest/Response` — Set parameter value
- `DataParameterResetRequest/Response` — Reset parameter to default
- `DataParameterSubscribeRequest/Response` — Subscribe to parameter changes
- `DataParameterUnsubscribeRequest/Response` — Unsubscribe from changes
- `DataParameterNotification` — Parameter change notification
- `DataParameterStatus` — Parameter status
- `DataParameterValue` — Parameter value wrapper
- `DataApplicationSubscribeRequest/Response` — Subscribe to app data
- `DataApplicationUnsubscribeRequest/Response` — Unsubscribe from app data
- `DataApplicationNotify` — Application notification
- `DataNotification` — Generic data notification

#### Resource Service (`Arturia.Collage.Protobuf.Resource*`)
- `ResourceStoreRequest/Response` — Store resource (presets, samples, etc.)
- `ResourceRetrieveRequest/Response` — Retrieve resource
- `ResourceRemoveRequest/Response` — Remove resource
- `ResourceListRequest/Response` — List available resources
- `ResourceItemInfo` — Resource metadata
- `ResourceItemType` — Resource type enum
- `ResourceLocation` — Resource location info
- `ResourceOptions` — Resource operation options
- `ResourceResult` — Operation result

#### System Service (`Arturia.Collage.Protobuf.System*`)
- `SystemVersionRequest/Response` — Get firmware/software version
- `SystemVersionInfo` — Version information structure
- `SystemVersionType` — Version type enum
- `SystemVersionValue` — Version value
- `SystemCommandExecuteRequest/Response` — Execute system command
- `SystemCommandTerminateRequest/Response` — Terminate process
- `SystemRestartRequest/Response` — Restart device
- `SystemShutdownRequest/Response` — Shutdown device
- `SystemStatusMemoryRequest/Response` — Memory status
- `SystemStatusStorageRequest/Response` — Storage status
- `SystemStatusProcessorRequest/Response` — Processor status
- `SystemCommandStatusRequest` — Command execution status
- `SystemNotification` — System notification
- `SystemProcessStatus` — Process status
- `SystemProcessEncryption` — Process encryption state

#### Security Service (`Arturia.Collage.Protobuf.Security*`)
- `SecurityAuthenticationRequest/Response` — Device authentication
- `SecurityEncryption` — Encryption configuration
- `SecurityResult` — Security operation result

### 3.4 USB Communication Details

**USB device identification pattern:**
```
\\?\%*3[USBusb]#%*3[VIDvid]_%4hx&%*3[PIDpid]_%4hx&%*s
```
This reveals Arturia uses standard USB device path enumeration with VID/PID matching.

**USB Configuration:**
- `collage.comm.usb` — USB communication key
- `collage.comm.usb.ll.keepalive` — Keepalive setting
- `collage.comm.usb.nopayload` — No-payload mode flag

**USB Classes:**
- `Arturia::USB::BulkInterface` — USB bulk transfer interface
- `Arturia::USB::DfuInterface` — DFU (firmware update) interface
- `Arturia::USB::LibusbDfuInterface` — libusb DFU implementation
- `Arturia::USB::TUSBDfuInterface` — TUSB audio DFU
- `Arturia::USB::LibusbDeviceManager` — Device enumeration
- `Arturia::USB::HotplugHandler` — USB hotplug detection
- `Arturia::USB::EndpointDescriptor` — USB endpoint configuration
- `Arturia::USB::InterfaceDescriptor` — USB interface configuration
- `Arturia::USB::DeviceIdentifier` — Device identification
- `Arturia::USB::UniqueDeviceIdentifier` — Unique device identification
- `Arturia::USB::AudioInterface` — Audio class interface
- `Arturia::USB::TUSBAudioInterface` — TUSB audio interface
- `Arturia::USB::TUSBDeviceManager` — TUSB device management
- `Arturia::USB::ConfigDescriptor` — USB configuration descriptor

**libusb Functions Used:**
- `libusb_bulk_transfer` — Bulk endpoint transfers
- `libusb_control_transfer` — Control transfers
- `libusb_claim_interface` / `libusb_release_interface`
- `libusb_open` / `libusb_close`
- `libusb_init` / `libusb_exit`
- `libusb_get_device_list` / `libusb_free_device_list`
- `libusb_get_device_descriptor` / `libusb_get_config_descriptor`
- `libusb_get_string_descriptor_ascii`
- `libusb_hotplug_register_callback`
- `libusb_set_configuration`
- `libusb_detach_kernel_driver`
- `libusb_set_debug`
- `libusb_handle_events_timeout`

---

## 4. Firmware Update Protocol

### 4.1 Firmware Update Classes

| Class | Purpose |
|-------|---------|
| `Arturia::FwUpdate::DFUUpdater` | DFU-based firmware update |
| `Arturia::FwUpdate::RKUpdater` | Rockchip-based firmware update |
| `Arturia::FwUpdate::CollageUpdater` | Collage protocol firmware update |
| `Arturia::FwUpdate::ArturiaUpdater` | Generic Arturia updater |
| `Arturia::FwUpdate::FirmwareUpdateController` | VST firmware update controller |
| `Arturia::MiniFreak::MiniFreakFirmwareUpdateComponent` | MiniFreak-specific firmware GUI |

### 4.2 Update Parameters

- `Arturia::FwUpdate::DfuUpdateParameters` — DFU update config
- `Arturia::FwUpdate::RKUpdateParameters` — Rockchip update config
- `Arturia::FwUpdate::CollageUpdateParameters` — Collage update config
- `Arturia::FwUpdate::UpdateParameters` — Generic update config

### 4.3 DFU Commands

| Command | Description |
|---------|-------------|
| `[dfu].checkhash` | Verify firmware hash |
| `[dfu].install` | Install firmware |
| `[dfu].reboot` | Reboot device |
| `[dfu].rebootloader` | Reboot into bootloader |
| `[dfu].reset_fw_from_dfu` | Reset firmware from DFU mode |
| `[dfu].set_master_vers` | Set master firmware version |
| `[dfu].set_progression` | Set update progress |
| `[dfu].pre_image_update` | Pre-update hook |
| `[dfu].post_image_update` | Post-update hook |

### 4.4 TUSBAUDIO DFU API

- `TUSBAUDIO_GetDfuStatus` — Get DFU state
- `TUSBAUDIO_GetFirmwareImage` — Get firmware image
- `TUSBAUDIO_GetFirmwareImageSize` — Get image size
- `TUSBAUDIO_LoadFirmwareImageFromBuffer` — Load from memory
- `TUSBAUDIO_LoadFirmwareImageFromFile` — Load from file
- `TUSBAUDIO_StartDfuDownload` — Begin DFU download
- `TUSBAUDIO_StartDfuRevertToFactoryImage` — Factory reset
- `TUSBAUDIO_StartDfuUpload` — Upload firmware
- `TUSBAUDIO_UnloadFirmwareImage` — Unload image
- `TUSBAUDIO_EndDfuProc` — End DFU process

### 4.5 RKUpdater (Rockchip) Flow

```
1. RKUpdater::UpdateSetup — Initialize update
   - Find serial device from registry
   - Check if already in loader mode
   - Reboot into loader mode if needed
2. RKUpdater::WaitRebootInLoader — Wait for loader device
3. RKUpdater::SendCommand — Execute update commands via Collage
4. RKUpdater::UpdateTearDown — Finalize update
```

### 4.6 Firmware File Format

- Firmware packages contain `info.json` with metadata
- `info.json` includes `productid` for validation
- Hash checking supported: `"Error: cannot check hash for component"`
- Firmware update URL: `https://support.arturia.com/hc/en-us/articles/11703736440476-MiniFreak-Firmware-update`

### 4.7 Protection/ASC Integration

- `update_firmware_prompt` — ASC firmware update prompt
- `update_firmware_status` — ASC firmware status tracking
- `update_firmware_trigger` — ASC firmware trigger command
- `kUpdateFirmwarePromptCommandName` — ASC command names
- `Arturia::Protection::Onboarding::FirmwareUpdateFlowHandler` — Onboarding firmware flow

---

## 5. Preset Transfer Protocol

### 5.1 Preset Management Classes

| Class | Purpose |
|-------|---------|
| `Arturia::MiniFreak::MiniFreakPresetBrowserController` | HW preset browser control |
| `Arturia::MiniFreak::MiniFreakPresetHwVstConverter` | HW ↔ VST preset conversion |
| `Arturia::MiniFreak::MiniFreakHardwarePresetsView` | Hardware presets GUI |
| `Arturia::MiniFreak::MiniFreakHardwareBackupsList` | Backup management GUI |
| `Arturia::MiniFreak::MiniFreakHwBankDetailComponent` | Bank detail view |
| `Arturia::MiniFreak::MFVPresetConverter` | Preset format conversion |
| `Arturia::JuceArturiaLib::PresetData` | Preset data model |
| `Arturia::JuceArturiaLib::LocalPresetManager` | Local preset management |
| `Arturia::JuceArturiaLib::MiniPresetManager` | Compact preset manager |
| `Arturia::JuceArturiaLib::PresetBrowserController` | General preset browser |

### 5.2 Preset Operations

| Function | Description |
|----------|-------------|
| `MiniFreakPresetBrowserController::LoadHWPresetsFromBank` | Load presets from hardware bank |
| `MiniFreakPresetBrowserController::UpdateBankJson` | Update bank metadata |
| `MiniFreakPresetBrowserController::DuplicateBankDirectory` | Duplicate a bank |
| `MiniFreakPresetBrowserController::ExportBackup` | Export backup |
| `MiniFreakPresetBrowserController::ImportBackup` | Import backup |
| `MiniFreakPresetBrowserController::UpdatePreset` | Update preset on hardware |
| `MiniFreakHardwarePresetsView::ImplAddToBank` | Add preset to hardware bank |
| `MiniFreakHardwarePresetsView::ImportPresets` | Import presets from files |
| `MiniFreakPresetHwVstConverter::ConvertPresetFromDataToSDK` | Convert HW preset to VST |
| `MiniFreakPresetHwVstConverter::ConvertPresetFromSDKToData` | Convert VST preset to HW |

### 5.3 Hardware Bank JSON Format

```cpp
Arturia::JuceArturiaLib::JsonFile<struct Arturia::MiniFreak::JsonData::HardwareBank>
```
Hardware bank metadata is stored as JSON (`HardwareBank` struct).

### 5.4 Preset File Formats

- `.mnfx` — MiniFreak preset file format
- `.mnfdump` — MiniFreak preset dump format
- File filter: `*.mnfx,*.mnfdump`

### 5.5 Sample/Folder Management

| Function | Description |
|----------|-------------|
| `StorageController::SendLocalSampleFolder` | Send local samples to hardware |
| `StorageController::RecomputeSamplesStorage` | Recompute sample storage stats |
| `StorageController::RecomputeWavetableStorage` | Recompute wavetable storage stats |
| `MiniFreakHardwarePresetsView::UploadFactorySampleFolder` | Upload factory samples |
| `MiniFreakController::UpdateSampleFromAudioFileName` | Update sample reference |

### 5.6 Key Preset/Bank UI Strings

- `"Are you sure you want to overwrite your MiniFreak bank with "` — Bank overwrite confirmation
- `"Add to bank"` / `"Copy To Bank"` — Bank operations
- `"Import Presets from files"` — Preset import
- `"Hardware Bank Name"` — Bank naming
- `"Writing factory samples to the MiniFreak, please wait..."` — Sample upload progress
- `"Presets backup imported successfully."` — Backup completion
- `"Choose bank to add your presets"` — Bank selection

---

## 6. Resource Transfer Protocol

The `ResourceTransferer` class manages high-level resource transfers between VST and hardware:

```
ResourceTransferer initialization sequence:
1. init communication channel
2. init command manager channel
3. init data handler
4. init resource handler
5. init resource control
6. init security handler
7. init system handler
8. init system handler sync
9. add resource handler to message handlers
10. start reception thread
```

**Related classes:**
- `Arturia::HwVstTools::ResourceTransferer` — Main transfer orchestrator
- `Arturia::HwVstTools::IResourceXferListener` — Transfer event listener
- `Arturia::HwVstTools::CommandExecution` — Command execution wrapper
- `Arturia::HwVstTools::FirmwareUpdateController` — Firmware update via resource transfer

---

## 7. Source Code Structure (from debug paths)

### Project Modules

```
minifreakv/
├── arturiausblib/src/libusb_wrapper/    # USB abstraction layer
│   ├── LibusbImpl.cpp
│   └── LibusbWrapper.cpp
├── basictools/                           # Basic utilities
├── collage/                              # USB communication protocol
│   ├── src/comm/CommUsb.cpp             # USB transport
│   ├── src/comm/CommTcp.cpp             # TCP transport
│   ├── src/protocol/ProtocolProtobuf.cpp # Protobuf protocol
│   ├── src/protocol/ProtocolRaw.cpp     # Raw protocol
│   ├── src/protocol/control/resource/   # Resource control
│   ├── src/protocol/control/system/     # System control
│   ├── src/protocol/data/               # Data protocol
│   └── src/protocol/security/           # Security protocol
├── hwvsttools/                           # Hardware-VST bridge
│   ├── src/HwVstController.cpp
│   └── src/UpdateComponent.cpp
├── jucearturialib/                       # Arturia's JUCE extensions
│   ├── src/Midi/                         # MIDI handling
│   ├── src/PresetBrowser/                # Preset browser
│   ├── src/Preset/                       # Preset management
│   └── src/SampleBrowser/               # Sample browser
├── minifreakv/src/                       # MiniFreak-specific code
│   ├── controller/
│   │   ├── MiniFreakController.cpp       # Main controller
│   │   ├── MiniFreakPresetHwVstConverter.cpp
│   │   ├── MiniFreakUIBuilder.cpp
│   │   ├── browser/
│   │   │   ├── MiniFreakHardwarePresetsView.cpp
│   │   │   ├── MiniFreakHardwareBackupsList.cpp
│   │   │   └── MiniFreakPresetBrowserController.cpp
│   │   ├── gui/
│   │   │   └── MiniFreakFirmwareUpdateComponent.cpp
│   │   └── hardware/
│   │       ├── StorageController.cpp     # Sample/wavetable storage
│   │       └── CommandQueue.cpp          # Hardware command queue
│   └── build64/Release/minifreakv_vst3.pdb
├── wrapperlib/src/                       # VST wrapper
│   ├── Midi/OutputMidiManager.cpp        # MIDI output management
│   └── Midi/OutputHWManager.cpp          # Hardware output
├── updatemanager/                        # Software update manager
├── protobuf/                             # Google Protobuf library
├── poco/                                 # POCO C++ libraries
├── boost/                                # Boost libraries
└── ziptool/                              # ZIP file handling
```

---

## 8. Key Findings Summary

### Communication Architecture
1. **Dual protocol stack**: The MiniFreak V uses BOTH:
   - **MIDI SysEx** (F0 00 20 6B ...) for parameter control and hardware sync
   - **Collage Protocol** (Protobuf over USB bulk) for resource transfer (presets, samples, firmware)

2. **USB Bulk Transfer** is used for heavy data operations (presets, samples, firmware), while **MIDI SysEx** handles real-time parameter control.

3. **libusb** is used directly (dynamically loaded) for USB communication, NOT the Windows MIDI API for hardware communication.

### SysEx Protocol
- Arturia manufacturer ID: `00 20 6B` (3-byte ID)
- MiniFreak device ID: `0x02`
- Broadcast ID: `0x7F`
- Multiple message types identified: parameter get/set (0x02, 0x08), requests (0x42)
- Groups: parameters (0x02), RPN (0x03), system (0x04), extended/firmware (0x0A)

### Firmware Update
- Three updater types: DFU, Rockchip (RKUpdater), Collage-based
- DFU commands for hash checking, version setting, bootloader management
- Firmware packages validated via `info.json` with product ID
- Update triggered through Arturia Software Center (ASC) integration

### Preset Transfer
- Presets use `.mnfx` format (with `.mnfdump` as dump format)
- Hardware bank metadata stored in JSON (`HardwareBank` struct)
- Bidirectional conversion between HW and VST preset formats
- Factory sample upload capability
- Sample and wavetable storage tracking

### Notable URLs
- Firmware update: `https://support.arturia.com/hc/en-us/articles/11703736440476-MiniFreak-Firmware-update`
- Website: `https://www.arturia.com`
- Contact: `mailto:contact@arturia.com`

---

## 9. String Count Summary

| Category | Count |
|----------|-------|
| SysEx related | 36 |
| MIDI related | 281 |
| Firmware/DFU | 83 |
| USB/Bulk | 146 |
| Preset | 861 |
| MiniFreak specific | 469 |
| Bank/Backup | 192 |
| Collage Protocol | 496 |
| USB Arturia classes | 128 |
| Source paths | 375 |
| **Total (unique)** | **~3,067** |

Full string data saved to: `/home/jth/hoon/minifreak/firmware/analysis/phase5_dll_strings.json`
