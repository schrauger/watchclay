watchclay for Wemo
=========
Watches a [Claymore Ethereum mining](https://github.com/nanopool/Claymore-Dual-Miner) rig for issues, and as needed, resets the rig by power cycling a wemo outlet using [If This Then That](https://ifttt.com). Also summarizes useful Claymore health data.

![watchclay schematic](https://raw.githubusercontent.com/schrauger/watchclay/master/images/watchclay_schematic.png)

Purpose
-------
Sometimes a Claymore Ethereum mining rig can become unstable or unresponsive, particularly when optimizing GPU performance by overclocking and undervolting. If the inactivity goes unnoticed, or if a person can't get immediate physical access to cycle the power, the resulting idleness wastes potential mining capacity.

This watchclay software watches Claymore via its remote management port (default 3333), which provides updates in JSON and HTML format. It watches for several kinds of issues:

- Claymore and/or the rig become unresponsive, and return no data.
- The hash rate falls below some expected performance.
- The mining pool rejects submitted shares.
- The temperature of one or more GPUs exceeds some maximum amount.

For most of these, watchclay rechecks a configurable number of times, and if the issue persists, it power cycles the wemo outlet to reset the rig and return Claymore to mining. In case of GPU overheating, watchclay immediately powers down the outlet to prevent permanent damage.

Email updates are sent whenever an issue persists and the rig is power cycled, and again when the rig returns to normal. An email update is also sent periodically to indicate normal operation.

A high-level summary of Claymore rig health can be monitored using tail -f on a logfile of watchclay output. The summary includes overall hashrate, slowest GPU, shares accepted and rejected by the mining pool, and the temperature of the hottest GPU.

![watchclay tail -f output](https://raw.githubusercontent.com/schrauger/watchclay/master/images/watchclay_tailf.png)

Launch and Compatibility
--------
Typical launch command:

`python -u watchclay.py watchclay.conf >watchclay.log 2>&1 &`

The -u option prevents output buffer delay.

If no configuration file is explicitly named, watchclay looks for the default file watchclay.conf (configuration details below).

Functioning email service is expected at /usr/sbin/sendmail.

watchclay has been tested with Claymore miner versions 10.0, 9.8, and 9.7. The software is written in Python, and has been tested with Python 2.7.10 on MacOS Sierra and with Python 2.7.12 on Ubuntu 16.04. It must run somewhere besides the mining rig; otherwise the power cycle becomes suicidal. For example, a small instance on Amazon Web Services with VPN access to the rig and wemo outlet works well.

Configuration
--------

## If This Then That

If This Then That (IFTTT) is a service that is used for automating many devices and services. Wemo supports this service, so this script uses IFTTT to tell Wemo to power off and on.

You must have an IFTTT account, and then you must link the Wemo Insight or other smart plug to your IFTTT account. You must also connect the Webhooks Maker service.

Create two applets, one for powering off and one for powering on.

### Power Off

* The `this` part will be a Webhooks Maker Event. Name it `wemo_power_off_request`.
* The `that` part will be a Wemo hook. Select your Wemo device, and tell it to power off.

### Power On

* The `this` part will be a Webhooks Maker Event. Name it `wemo_power_on_request`.
* The `that` part will be a Wemo hook. Select your Wemo device, and tell it to power on.

## Config File

Edit the watchclay.conf file to match the configuration to your environment and requriements.

### If This Then That

`webhooks_key` The unique key to your IFTTT webhooks url. This is found in the [webhooks IFTTT settings page](https://ifttt.com/services/maker_webhooks/settings).

`webhooks_power_off_string` The event name passed to webhooks for powering off your wemo. You must define two IFTTT recipes, one for powering off and one for powering on. The string passed to webhooks must match the one defined here.

`webhooks_power_on_string` The event name passed to webhooks for powering on your wemo.

### Claymore

`claymore_ip` The IP address of your Claymore mining rig.

`claymore_port` The TCP port for Claymore reporting. The default is **3333**.

### Limits

`hash_floor` The minimum acceptable hashrate in Mh/s for the total mining rig. A typical starting point for AMD RX570/580 is **20 Mh/s multiplied by the number of GPUs**. Catches a floundering GPU when Claymore can't remedy.

`reject_ceiling` The maximum acceptable number of shares rejected by the mining pool. Malformed shares can be an undesirable side-effect of overclocking.

`temp_ceiling` The maximum acceptable temperature for any GPU, in degrees Celsius. Unlike the other limits, exceeding the temperature ceiling results in immediate power shut down to avoid permanent damage.

### Timers

`check_time` Seconds between Claymore mining rig status checks. Suggested value is **10 seconds**.

`max_recheck` Maximum rechecks allowed when an issue arises before the rig is reset by power cycle. Too few rechecks results in hair-trigger resets, when waiting would have allowed the issue to resolve itself. Also, check_time multipled by max_recheck must be long enough to allow the rig to reboot and Claymore to restart, or else watchclay will cause an endless loop of resets. Suggested value is **12 rechecks**, which resets the rig after about two minutes of an issue persisting.

`cycle_time` Seconds to pause during a reset between power off and power on. Allows the power supply capacitors to discharge for a clean restart. Suggested value is **30 seconds**.

`wait_time` Seconds to wait before an API call to mPower or Claymore times out with no response. Suggested value is **10 seconds**.

`update_time` Seconds between email updates during normal operation. Suggested value is **3600 seconds** for hourly updates.

### Email

`sender` Email address to send updates from watchclay.

`recipients` One or more email addresses to receive updates from watchclay.

`reference` Text to include in email body for your reference. For example, you could include the URLs for your mining pool dashboard and Ethereum account balance, for easy reference. Indent subsequent lines to include multiple lines.

Feedback
--------
Feedback welcome about bugs or feature requests, via the [Issues](https://github.com/schrauger/watchclay/issues) tab.

If watchclay helped you mine more efficiently, tips are always welcome! :moneybag: :beer: :smile:

Original Author Ether `0x61a7d5222cbbC4c86AF8f26954D4BA2a8983DBC9`

Wemo Support Author Ether `0x66a1Be3E3a6174afd579bBd31137F614Cb5c5031`

Happy mining!

----------
Copyright 2017 Larry Lang

Wemo support added by Stephen Schrauger

