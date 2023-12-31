from math import log
import time

MAX_PACKET_LEN  = 300
PACKET_SIGNATURE_OFFSET = 4
NODE_OFFSET = 9
VREF_OFFSET = 18
TEMPERATURE_OFFSET = 20
LIGHT_OFFSET = 22

SEEKING_START_BYTE             = 1
SEEKING_PACKET_TYPE            = 2
SEEKING_DESTINATION_ADDRESS    = 3
SEEKING_AM_TYPE                = 4
SEEKING_AM_GROUP               = 5
SEEKING_PAYLOAD_LENGTH         = 6
SEEKING_PAYLOAD                = 7
SEEKING_CRC                    = 8
SEEKING_END_BYTE               = 9

LUNIX_SENSOR_CNT = 2;

class LunixStateMachine:
	def __init__(self):
		self.pos = 0
		self.next_is_special = 0
		self.set_state(SEEKING_START_BYTE, 1, 0)
		self.packet = bytearray(MAX_PACKET_LEN)

		self.sensors = {}
	
	def set_state(self, state, btr, br):
		self.state = state
		self.bytes_to_read = btr
		self.bytes_read = br

	def parse_state(self, data, i, use_specials):
		iter = 0
		while i[0] < len(data) and self.bytes_read < self.bytes_to_read:
			iter += 1
			if iter == 50: return -1

			if self.pos == MAX_PACKET_LEN:
				self.pos = 0
				return -1

			if 1 == use_specials:
				if self.next_is_special:
					if 0x7E == self.next_is_special:
						self.packet[self.pos] = data[i[0]]
					if 0x7D == self.next_is_special:
						self.packet[self.pos] = data[i[0]]^0x20
					self.pos += 1
					self.bytes_read += 1
					i[0] += 1 #done because lists are mutable
					self.next_is_special = 0
				else:
					if 0x7E == data[i[0]] or 0x7D == data[i[0]]:
						self.next_is_special = data[i[0]]
						i[0] += 1
					else:
						self.packet[self.pos] = data[i[0]]
						self.pos += 1
						self.bytes_read += 1
						i[0] += 1
			else:
				self.packet[self.pos] = data[i[0]]
				self.pos += 1
				self.bytes_read += 1
				i[0] += 1

		if self.bytes_read == self.bytes_to_read:
			return 1

		return 0

	def receive(self, buf):
		i = [0]

		if self.state == SEEKING_START_BYTE:
			if self.parse_state(buf, i, 0) == 1:
				self.set_state(SEEKING_PACKET_TYPE, 1, 0)

		if self.state == SEEKING_PACKET_TYPE:
			if self.parse_state(buf, i, 0) == 1:
				self.set_state(SEEKING_DESTINATION_ADDRESS, 2, 0)

		if self.state == SEEKING_DESTINATION_ADDRESS:
			if self.parse_state(buf, i, 1) == 1:
				self.set_state(SEEKING_AM_TYPE, 1, 0)

		if self.state == SEEKING_AM_TYPE:
			if self.parse_state(buf, i, 1) == 1:
				self.set_state(SEEKING_AM_GROUP, 1, 0)

		if self.state == SEEKING_AM_GROUP:
			if self.parse_state(buf, i, 1) == 1:
				self.set_state(SEEKING_PAYLOAD_LENGTH, 1, 0)

		if self.state == SEEKING_PAYLOAD_LENGTH:
			if self.parse_state(buf, i, 1) == 1:
				payload_length = self.packet[self.pos - 1]
				self.set_state(SEEKING_PAYLOAD, payload_length, 0)

		if self.state == SEEKING_PAYLOAD:
			if self.parse_state(buf, i, 1) == 1:
				self.set_state(SEEKING_CRC, 2, 0)

		if self.state == SEEKING_CRC:
			if self.parse_state(buf, i, 1) == 1:
				self.set_state(SEEKING_END_BYTE, 1, 0)

		if self.state == SEEKING_END_BYTE:
			if self.parse_state(buf, i, 0) == 1:
				self.update_sensors()
				self.pos = 0
				self.next_is_special = 0
				self.set_state(SEEKING_START_BYTE, 1, 0)

		return 0

	@staticmethod
	def uint16_from_packet(buf, offset):
		return int.from_bytes(buf[offset:offset+2], byteorder='little', signed=False)

	def update_sensors(self):
		nodeid = self.uint16_from_packet(self.packet, NODE_OFFSET)
		if 0<=nodeid<LUNIX_SENSOR_CNT:
			batt = self.uint16_to_batt(self.uint16_from_packet(self.packet, VREF_OFFSET))
			temp = self.uint16_to_temp(self.uint16_from_packet(self.packet, TEMPERATURE_OFFSET))
			light = self.uint16_to_light(self.uint16_from_packet(self.packet, LIGHT_OFFSET))

			self.sensors[nodeid] = {"battery": batt, "temp": temp, "light": light, "last_update": time.time()}

	@staticmethod
	def uint16_to_batt(value):
		if value != 0:
			return 1.223 * (1023.0 / value)
		else: return -0

	@staticmethod
	def uint16_to_light(value):
		return value * 5000.0 / 65535

	@staticmethod
	def uint16_to_temp(value):
		R1 = 10000.0
		ADC_FS = 1023.0

		a = 0.001010024
		b = 0.000242127
		c = 0.000000146
		
		Rth = (R1 * (ADC_FS - value)) / value
		Kelvin_Inv = a + b * log(Rth) + c * log(Rth)**3

		res = (1.0 / Kelvin_Inv) - 272.15
		
		return -272.15 if res < -272.15 else res
