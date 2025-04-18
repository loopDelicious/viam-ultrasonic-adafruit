# Module ultrasonic-adafruit

Use the [Adafruit CircuitPython library](https://github.com/adafruit/Adafruit_CircuitPython_HCSR04) for controlling HC-SR04 ultrasonic range sensors

## Model joyce:ultrasonic-adafruit:ultrasonic-adafruit

Get sensor readings from an ultrasonic sensor.

### Configuration

The following attribute template can be used to configure this model:

```json
{
  "board": <string>,
  "echo_interrupt_pin": <string>,
  "trigger_pin": <string>
}
```

#### Attributes

The following attributes are available for this model:

| Name                 | Type   | Inclusion | Description                                                            |
| -------------------- | ------ | --------- | ---------------------------------------------------------------------- |
| `board`              | string | Required  | Name of the Raspberry Pi board according to the Viam app               |
| `echo_interrupt_pin` | string | Required  | Number of the echo pin that maps to GPIO pin, must be in Dxx format    |
| `trigger_pin`        | string | Required  | Number of the trigger pin that maps to GPIO pin, must be in Dxx format |

#### Example Configuration

```json
{
  "board": "board-1",
  "echo_interrupt_pin": "D24",
  "trigger_pin": "D23"
}
```
