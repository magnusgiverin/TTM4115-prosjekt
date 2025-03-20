MQTT messages are in JSON format from Scooter (PI-1) to server (PI-2)

{
    command: enum("Lock", "Unlock")
    coordinates: [int, int]
}