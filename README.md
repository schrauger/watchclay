watchclay
=========
Watches a [Claymore Ethereum mining](https://github.com/nanopool/Claymore-Dual-Miner) rig for issues, and as needed, resets the rig by power cycling an outlet on a [Ubiquiti mPower](https://www.ubnt.com/mfi/mpower/) strip.

![watchclay schematic](https://raw.githubusercontent.com/llang629/watchclay/master/images/watchclay_schematic.png)

Purpose
-------
Sometimes a Claymore Ethereum mining rig can become unstable or unresponsive, particularly when optimizing GPU performance by overclocking and undervolting. If the inactivity goes unnoticed, or if a person can't get immediate physical access to cycle the power, the resulting idleness wastes potential mining capacity.

This watchclay software watches Claymore via its remote management port (default 3333), which provides updates in JSON and HTML format. It watches for several kinds of issue:

- Claymore and/or the rig become unresponsive, and return no data.
- The hash rate falls below some expected performance.
- The mining pool rejects submitted shares.
- The temperature of one or more GPUs exceeds some maximum amount.

For most of these issues, watchclay rechecks a configurable number of times, and if the issues persist, it power cycles the designated outlet on the mPower strip to reset the rig and return Claymore to mining. In case of GPU overheating, watchclay immediately powers down the designated outlet to prevent permanent damage.

Email updates are sent whenever an issue persists and the rig is power cycled, and again when the rig returns to normal. An email update is also sent periodically to indicate normal operation.

A high-level summary of Claymore rig health can be monitored using tail -f on a logfile of watchclay output. The summary includes overall hashrate, slowest GPU, shares accepted and rejected by the mining pool, the temperature of the hottest GPU, and total amps drawn. (Rig power consumption in watts equals current in amps multiplied by line voltage.)

![watchclay tail -f output](https://raw.githubusercontent.com/llang629/watchclay/master/images/watchclay_tailf.png)

Requirements and Compatibility
--------
watchclay is written in Python, and has been tested on MacOS Sierra with Python 2.7.10 and Ubuntu 16.04 with Python 2.7.12. It must run somewhere besides the mining rig (otherwise the power cycle becomes suicidal). For instance, a small instance on Amazon Web Services with VPN access to the rig works well.

Typical launch command:
`python -u watchclay.py watchclay.conf >watchclay.log 2>&1 &`
(The -u option prevents output buffer delay.)

Feedback
--------
Feedback welcome about bugs or feature requests, via the [Issues tab](https://github.com/llang629/watchclay/issues).

If watchclay helped you mine more efficiently, tips are also welcome! :moneybag: :beer: :smile:

Ether `0x61a7d5222cbbC4c86AF8f26954D4BA2a8983DBC9`


----------
Copyright 2017 Larry Lang
