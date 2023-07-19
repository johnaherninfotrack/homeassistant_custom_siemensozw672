[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

**This component will set up the following platforms.**

| Platform        | Description                         |
| --------------- | ----------------------------------- |
| `binary_sensor` | Show something `True` or `False`.   |
| `sensor`        | Show info from API.                 |
| `switch`        | Switch something `True` or `False`. |
| `select`        | Select one or more enumerations.    |
| `number`        | A number - eg. a temperature        |


![example][exampleimg]

{% if not installed %}

## Installation

1. Click install.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Siemens OZW672".

{% endif %}

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



<!---->

## Credits

This project was created in my spare time on an OZW671.01 monitoring my home Hydronic Plant.  

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[commits-shield]: https://img.shields.io/github/commit-activity/y/johnaherninfotrack/homeassistant_custom_siemensozw672.svg?style=for-the-badge
[commits]: https://github.com/:q/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license]: https://github.com/johnaherninfotrack/homeassistant_custom_siemensozw672/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/johnaherninfotrack/homeassistant_custom_siemensozw672.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40johnaherninfotrack-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/johnaherninfotrack/homeassistant_custom_siemensozw672.svg?style=for-the-badge
[releases]: https://github.com/johnaherninfotrack/homeassistant_custom_siemensozw672/releases
[user_profile]: https://github.com/johnaherninfotrack
