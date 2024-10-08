from zaber_motion import Library
from zaber_motion.ascii import Connection
import constants, functions
import sys

if __name__ == "__main__":
    Library.enable_device_db_store()
    # Establish Connections and Start Program
    n = len(sys.argv)
    arg = ""
    if n > 1:
        arg = sys.argv[1]

    if arg in {"-p", "--physical"}:
        try:
            with Connection.open_serial_port("COM3") as connection:
                connection.enable_alerts()
                device_list = connection.detect_devices()
                print("RUNNING ON PHYSICAL DEVICE")
                functions.stage_controller(device_list)

        except Exception as e:
            print(f"Error with physical device connection: {e}")
    elif arg in {"-v", "--virtual"}:
        try:

            with Connection.open_iot(
                constants.TEST_ID, token=constants.TEST_TOKEN
            ) as connection:
                connection.enable_alerts()
                device_list = connection.detect_devices()
                print("RUNNING ON VIRTUAL DEVICE")
                functions.stage_controller(device_list)

        except Exception as e:
            print(f"Error with virtual device connection: {e}")

    else:
        print(
            "WRONG ARGUMENT. Possible arguments are: -p/--physical: Physical, -v/--virtual: Virtual"
        )
