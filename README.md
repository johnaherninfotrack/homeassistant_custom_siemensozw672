# Siemens OZW672 Integration for HomeAssitant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]


**This component will set up the following platforms.**

OZW672 is a Web server platform which enables remote plant monitoring for Siemens LPB/BSB Plants.
This integration was built and tested using a OZW672.01 running v11.0 firmware monitoring an RVS43.345/109 with 
three AVS73.390/109 extension modules.  

Yes - you can use this integration to WRITE values to the OZW672.  Noting that:
1. The OZW672 only supports certain datapoints to have WriteAccess
2. This integration only supports writing for "Enumerations", "Numbers" and "Switch" domains.



| Platform        | Description                                                               |
| --------------- | ------------------------------------------------------------------------- |
| `binary_sensor` | Read only Show something `On` or `Off`.  eg a Pump                        |
| `sensor`        | Read only sensors that don't fit in any other category                    |
| `switch`        | Read/Writ eSwitch something `On` or `Off`.                                |
| `select`        | Read/Write selectable Enumerations                                        |
| `number`        | Read/Write Numbers - eg Temperature or Percentage                         |


![example][exampleimg]

## Installation

PREFERENCE:  Install via HACS.

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `siemens_ozw672`.
4. Download _all_ the files from the `custom_components/siemens_ozw672/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Siemens OZW672"

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/siemens_ozw672/translations/en.json
custom_components/siemens_ozw672/translations/fr.json
custom_components/siemens_ozw672/translations/nb.json
custom_components/siemens_ozw672/translations/sensor.en.json
custom_components/siemens_ozw672/translations/sensor.fr.json
custom_components/siemens_ozw672/translations/sensor.nb.json
custom_components/siemens_ozw672/translations/sensor.nb.json
custom_components/siemens_ozw672/__init__.py
custom_components/siemens_ozw672/api.py
custom_components/siemens_ozw672/binary_sensor.py
custom_components/siemens_ozw672/config_flow.py
custom_components/siemens_ozw672/const.py
custom_components/siemens_ozw672/manifest.json
custom_components/siemens_ozw672/sensor.py
custom_components/siemens_ozw672/switch.py
```

## Configuration is done in the UI

NOTE: 
1. The OZW672 is not very powerful - LIMIT polling only variables you require
2. In my testing http was more scaleable than https - YOU MUST ENABLE THIS IN THE OZW672
3. https implementation does NOT check for valid server certificate
4. The component provides flexbility in naming your entities in two ways:
    a. No Prefix.  eg. "Legionella function"
    b. Prefix the datapoint with the Function/MenuItem name eg.  "DHW - Legionella function"
    c. Prefix the datapoint with the Operating Line number from the manual eg. "1640 Legionella function"
    d. Both Prefixes - eg: "DHW - 1640 Legionella function"
5. You can discover entities to poll, then re-run and discover more.  

My recommendations for reliable operation:
1. Configure the OZW672 to use http. Home > 0.x OZW672.01 > Settings > Communication > Services > We access via http = ON
2. Configure the OZW672 to use static IP, Gateway & DNS. Home > 0.x OZW672.01 > Settings > Communication > Ethernet
3. Discover Functions one at a time.  The OZW672 is not powerful - discover one function and max 10 variables at a time.
4. Configure a dedicated user for your home assistant polling.  I used the "Service" user group.

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was created in my spare time on an OZW671.01 monitoring my home Hydronic Plant.  

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/johnaherninfotrack
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/johnaherninfotrack/homeassistant_custom_siemensozw672.svg?style=for-the-badge
[commits]: https://github.com/johnaherninfotrack/homeassistant_custom_siemensozw672/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/johnaherninfotrack/homeassistant_custom_siemensozw672.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40johnaherninfotrack-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/johnaherninfotrack/homeassistant_custom_siemensozw672.svg?style=for-the-badge
[releases]: https://github.com/johnaherninfotrack/homeassistant_custom_siemensozw672/releases
[user_profile]: https://github.com/johnaherninfotrack
