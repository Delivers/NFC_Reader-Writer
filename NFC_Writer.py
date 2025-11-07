from typing import Dict
import argparse

from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from smartcard.CardConnection import CardConnection
from smartcard.System import *
import ndef


def decode_atr(atr: str) -> Dict[str, str]:
    """Decode the ATR (Answer to Reset) string into readable components."""
    atr = atr.split(" ")

    rid = atr[7:12]
    standard = atr[12]
    card_name = atr[13:15]

    card_names = {
        "00 01": "MIFARE Classic 1K",
        "00 38": "MIFARE Plus® SL2 2K",
        "00 02": "MIFARE Classic 4K",
        "00 39": "MIFARE Plus® SL2 4K",
        "00 03": "MIFARE Ultralight®",
        "00 30": "Topaz and Jewel",
        "00 26": "MIFARE Mini®",
        "00 3B": "FeliCa",
        "00 3A": "MIFARE Ultralight® C",
        "FF 28": "JCOP 30",
        "00 36": "MIFARE Plus® SL1 2K",
        "FF[SAK]": "undefined tags",
        "00 37": "MIFARE Plus® SL1 4K",
        "00 07": "SRIX",
    }

    standards = {
        "03": "ISO 14443A, Part 3",
        "11": "FeliCa",
    }

    return {
        "RID": " ".join(rid),
        "Standard": standards.get(standard, "Unknown"),
        "Card Name": card_names.get(" ".join(card_name), "Unknown"),
    }


def get_card_uid(connection: CardConnection) -> str:
    """
    Read the UID of the NFC tag using a standard APDU command.

    Returns:
        str: UID as a hex string without spaces (e.g. '04A2B3C4D5E6F7'),
             or empty string if reading failed.
    """
    # APDU to get UID (for PC/SC readers like ACR122U)
    SELECT_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]

    response, sw1, sw2 = connection.transmit(SELECT_UID)
    if sw1 == 0x90 and sw2 == 0x00 and response:
        uid_hex_with_spaces = toHexString(response)      # '04 A2 B3 C4 ...'
        uid_compact = uid_hex_with_spaces.replace(" ", "").upper()
        # print(f"Card UID: {uid_hex_with_spaces} (compact: {uid_compact})")
        return uid_compact
    else:
        print(f"Failed to read UID, SW1: {sw1:02X}, SW2: {sw2:02X}")
        return ""


def build_url_with_uid(base_url: str, uid: str) -> str:
    """
    Append UID as a query parameter to the base URL.

    If the URL already has query parameters, '&uid=' is used,
    otherwise '?uid=' is used.

    Args:
        base_url (str): Original URL from CLI.
        uid (str): Compact UID hex string (no spaces).

    Returns:
        str: URL with appended uid parameter, or base_url if uid is empty.
    """
    if not uid:
        print("No UID available, writing base URL without uid parameter.")
        return base_url

    separator = "&" if "?" in base_url else "?"
    final_url = f"{base_url}{separator}uid={uid}"
    # print(f"Final URL to write (with UID): {final_url}")
    return final_url


def create_ndef_record(url: str) -> bytes:
    """Encodes a given URI into a complete NDEF message using ndeflib.

    Args:
        url (str): The URI to be encoded into an NDEF message.

    Returns:
        bytes: The complete NDEF message as bytes, ready to be written to an NFC tag.
    """
    uri_record = ndef.UriRecord(url)

    # Encode the NDEF message (single record)
    encoded_message = b"".join(ndef.message_encoder([uri_record]))

    # Calculate total length of the NDEF message (excluding start byte and terminator)
    message_length = len(encoded_message)

    # Create the initial part of the message with start byte, length, encoded message, and terminator
    initial_message = b"\x03" + message_length.to_bytes(1, "big") + encoded_message + b"\xFE"

    # Calculate padding to align to the nearest block size (assuming 4 bytes per block)
    padding_length = -len(initial_message) % 4
    complete_message = initial_message + (b"\x00" * padding_length)
    return complete_message


def write_ndef_message(connection: CardConnection, ndef_message: bytes) -> bool:
    """Writes the NDEF message to the NFC tag.

    Args:
        connection (CardConnection): The connection to the NFC tag.
        ndef_message (bytes): The NDEF message to be written.

    Returns:
        bool: True if the write operation is successful, False otherwise.
    """
    page = 4
    while ndef_message:
        block_data = ndef_message[:4]
        ndef_message = ndef_message[4:]
        write_command = [0xFF, 0xD6, 0x00, page, 0x04] + list(block_data)
        response, sw1, sw2 = connection.transmit(write_command)
        if sw1 != 0x90 or sw2 != 0x00:
            print(
                f"Failed to write to page {page}, "
                f"SW1: {sw1:02X}, SW2: {sw2:02X}"
            )
            return False
        # print(f"Successfully wrote to page {page}")
        page += 1
    return True


class NTAG215Observer(CardObserver):
    """Observer class for NFC card detection and processing."""

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def update(self, observable, actions):
        global cards_processed
        (addedcards, _) = actions

        for card in addedcards:
            # print(f"Card detected, ATR: {toHexString(card.atr)}")

            try:
                connection = card.createConnection()
                connection.connect()
                # print("Connected to card")

                # Optional: decode ATR info
                info = decode_atr(toHexString(card.atr))
                # print(
                    #f"Card Name: {info['Card Name']}, "
                    #f"Standard: {info['Standard']}, RID: {info['RID']}"
                #)

                # Read UID from the card
                uid = get_card_uid(connection)

                # Build final URL with UID as query parameter
                final_url = build_url_with_uid(self.url, uid)

                # Create and write NDEF (URL containing UID)
                ndef_bytes = create_ndef_record(final_url)
                if write_ndef_message(connection, ndef_bytes):
                    print(final_url)
                else:
                    print("Failed to write NDEF data to the tag.")

                cards_processed += 1
                # print(f"Total cards flashed: {cards_processed}")

            except Exception as e:
                print(f"An error occurred: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Write a URL (with tag UID as query parameter) as an NDEF record to an NTAG215 NFC tag."
    )
    parser.add_argument(
        "url",
        help="The base URL to write to the NFC tag (e.g. https://example.com)",
    )
    return parser.parse_args()


def main():
    global cards_processed
    cards_processed = 0

    args = parse_args()
    url_to_write = args.url

    # print(f"Starting NFC card processing...\nBase URL: {url_to_write}")
    cardmonitor = CardMonitor()
    cardobserver = NTAG215Observer(url_to_write)
    cardmonitor.addObserver(cardobserver)

    try:
        input("Present a tag to the reader.\nPress Enter to stop...\n")
    finally:
        cardmonitor.deleteObserver(cardobserver)
        # print(f"Stopped NFC card processing. Total cards processed: {cards_processed}")


if __name__ == "__main__":
    # Example: python NFC_Writer.py https://example.com
    main()
