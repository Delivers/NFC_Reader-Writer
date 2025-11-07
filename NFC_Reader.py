from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from smartcard.CardConnection import CardConnection
import ndef
from preferredsoundplayer import *


cards_processed = 0


def read_ndef_message(connection: CardConnection) -> bool:
    """
    Reads the NDEF message from the NFC tag and prints its contents.

    Returns:
        bool: True if an NDEF message was successfully read and parsed, False otherwise.
    """
    # Start reading from the usual starting page of the NDEF message (page 4 for NTAG21x)
    read_command = [0xFF, 0xB0, 0x00, 4, 0x04]
    message = b''

    try:
        while True:  # Loop to read all parts of the NDEF message
            response, sw1, sw2 = connection.transmit(read_command)

            if sw1 == 0x90 and sw2 == 0x00:
                # Append only the first 4 bytes (one page)
                message += bytes(response[:4])

                # Stop when we see the NDEF terminator TLV 0xFE
                if 0xFE in response:
                    break

                # Move to the next page
                read_command[3] += 1
            else:
                print(
                    f"Failed to read at page {read_command[3]}: "
                    f"SW1={sw1:02X}, SW2={sw2:02X}"
                )
                return False

        print(f"Raw NDEF TLV data (hex): {message.hex()}")

        # Basic TLV parsing for NDEF:
        # 0x03 = NDEF Message TLV
        # [1]   = length of the NDEF message
        # [2..] = NDEF message bytes
        if len(message) < 3 or message[0] != 0x03:
            print("No valid NDEF TLV (0x03) found at the beginning of the data.")
            return False

        ndef_length = message[1]
        ndef_start = 2
        ndef_end = ndef_start + ndef_length

        if ndef_end > len(message):
            print("NDEF length field is inconsistent with the data size.")
            return False

        encoded_message = message[ndef_start:ndef_end]
        print(f"NDEF payload (hex): {encoded_message.hex()}")

        # Decode and print all NDEF records
        try:
            records = list(ndef.message_decoder(encoded_message))
        except Exception as e:
            print(f"Error decoding NDEF message: {e}")
            return False

        if not records:
            print("No NDEF records found.")
            return False

        print("Decoded NDEF records:")
        for i, record in enumerate(records, start=1):
            print(f"  Record {i}: {record}")
            # If it's a URI record, show the URI clearly
            if isinstance(record, ndef.UriRecord):
                print(f"    URI: {record.iri}")

        return True

    except Exception as e:
        print(f"Error during reading: {e}")
        return False


def beep(success: bool) -> None:
    """
    Plays a sound based on the success status.

    Args:
        success (bool): Indicates whether the operation was successful or not.
    """
    if success:
        soundplay("ok.wav")
    else:
        soundplay("error.wav")


class NTAG215Observer(CardObserver):
    """Observer class for NFC card detection and processing."""

    def update(self, observable, actions):
        global cards_processed
        (addedcards, _) = actions

        for card in addedcards:
            print(f"Card detected, ATR: {toHexString(card.atr)}")

            try:
                connection = card.createConnection()
                connection.connect()
                print("Connected to card")

                if read_ndef_message(connection):
                    beep(True)
                else:
                    beep(False)

                cards_processed += 1
                print(f"Total cards processed: {cards_processed}")

            except Exception as e:
                print(f"An error occurred while handling the card: {e}")
                beep(False)


def main():
    print("Starting NFC card processing...")
    cardmonitor = CardMonitor()
    cardobserver = NTAG215Observer()
    cardmonitor.addObserver(cardobserver)

    try:
        input("Press Enter to stop...\n")
    finally:
        cardmonitor.deleteObserver(cardobserver)
        print("Stopped NFC card processing. Total cards processed:", cards_processed)


if __name__ == "__main__":
    main()
