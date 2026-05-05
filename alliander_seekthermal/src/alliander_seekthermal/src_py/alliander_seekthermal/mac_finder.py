#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import os
import subprocess

from rclpy.logging import RcutilsLogger


class MacAddressFinder:
    """Finds the IP address of a network device by its MAC address.

    First checks the local ARP cache via `ip neigh show`. If not found,
    falls back to an `arp-scan` sweep over all Ethernet and wireless
    interfaces to populate the cache and retry.
    """

    def __init__(self, logger: RcutilsLogger, target_mac: str) -> None:
        """Initializes the MacAddressFinder with a given logger and target MAC address.

        Args:
            logger (RcutilsLogger): Logger given by external class to print output to.
            target_mac (str): Target MAC address to look for.
        """
        self.logger = logger
        self.target_mac = target_mac.lower()

    def find_ip(self) -> str | None:
        """Search for the device IP, falling back to an ARP sweep if not cached.

        Returns:
            str | None: IP address of the matching device, or None if not found.
        """
        self.logger.info(f"Searching ARP cache for MAC {self.target_mac}.")
        ip_addr = self._check_arp_cache()

        if ip_addr is None:
            self.logger.info("Not found in ARP cache, running ARP sweep.")
            ip_addr = self._arp_scan()
        return ip_addr

    def _check_arp_cache(self) -> str | None:
        """Check the kernel ARP cache via `ip neigh show`.

        Returns:
            str | None: IP address if found, None otherwise.
        """
        result = subprocess.run(
            ["ip", "neigh", "show"], capture_output=True, text=True, check=False
        )
        return self._find_mac_in_output(result.stdout)

    def _arp_scan(self) -> str | None:
        """Run `arp-scan` over all Ethernet and wireless interfaces.

        Iterates over interfaces in /sys/class/net, scanning those whose
        names start with 'e' (Ethernet) or 'w' (wireless).

        Returns:
            str | None: IP address if found on any interface, None otherwise.
        """
        for iface in os.listdir("/sys/class/net"):
            if not (iface.startswith("e") or iface.startswith("w")):
                continue
            self.logger.info(f"Running ARP scan on interface {iface}.")
            result = subprocess.run(
                ["arp-scan", "--localnet", f"--interface={iface}"],
                capture_output=True,
                text=True,
                check=False,
            )
            ip_addr = self._find_mac_in_output(result.stdout)
            if ip_addr is not None:
                return ip_addr

        return None

    def _find_mac_in_output(self, output: str) -> str | None:
        """Search command output for a line containing the target MAC.

        Args:
            output (str): stdout from `ip neigh show` or `arp-scan`.

        Returns:
            str | None: IP address (first token of matching line), or None.
        """
        for line in output.splitlines():
            if self.target_mac in line.lower():
                ip = line.split()[0]
                self.logger.info(f"Found device at {ip}.")
                return ip
        return None
