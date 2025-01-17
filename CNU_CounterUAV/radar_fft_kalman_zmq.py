import zmq
import numpy as np
import pylab as pl
from scipy.io import wavfile
from pykalman import KalmanFilter
import threading
import spidev
import time

#https://github.com/kerrydwong/AD7705X
#https://github.com/belese/python-AD7705X

#SPI CODE
REG_CMM = 0x0  # communication register 8 bit
REG_SETUP = 0x1  # setup register 8 bit
REG_CLOCK = 0x2  # clock register 8 bit
REG_DATA = 0x3  # data register 16bit, contains conversion result
REG_TEST = 0x4  # test register 8 bit, POR 0x0
REG_NOP = 0x5  # no operation
REG_OFFSET = 0x6  # offset register 24 bit
REG_GAIN = 0x7  # gain register 24 bit

# channel selection for AD7705
#CH1 CH0
CHN_AIN1 = 0x0
CHN_AIN2 = 0x1

# output update rate
# CLK FS1 FS0
UPDATE_RATE_20 = 0X0  # 20 Hz
UPDATE_RATE_25 = 0X1  # 25 Hz
UPDATE_RATE_100 = 0X2  # 100 Hz
UPDATE_RATE_200 = 0X3  # 200 Hz
UPDATE_RATE_50 = 0X4  # 50 Hz
UPDATE_RATE_60 = 0X5  # 60 Hz
UPDATE_RATE_250 = 0X6  # 250 Hz
UPDATE_RATE_500 = 0X7  # 500 Hz

#operation mode options
#MD1 MD0
MODE_NORMAL = 0x0  # normal mode
MODE_SELF_CAL = 0x1  # self-calibration
MODE_ZERO_SCALE_CAL = 0x2  # zero-scale system calibration, POR 0x1F4000, set FSYNC high before calibration, FSYNC low after clibration
MODE_FULL_SCALE_CAL = 0x3  # full-scale system calibration, POR 0x5761AB, set FSYNC high before calibration, FSYNC low after calibration

# gain setting
GAIN_1 = 0X0
GAIN_2 = 0X1
GAIN_4 = 0X2
GAIN_8 = 0X3
GAIN_16 = 0X4
GAIN_32 = 0X5
GAIN_64 = 0X6
GAIN_128 = 0X7

UNIPOLAR = 0x0
BIPOLAR = 0x1

CLK_DIV_1 = 0x1
CLK_DIV_2 = 0x2

MODE = 0b11  # SPI_CPHA | SPI_CPOL
BITS = 8
SPEED = 50000
DELAY = 10

class spi_handler():
    def __init__(self, bus=0, device=0) :
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = SPEED
        self.spi.mode = MODE
        self.spi.bits_per_word = BITS
        self.reset()

    def initChannel(self, channel, clkDivider=CLK_DIV_1, polarity=BIPOLAR, gain=GAIN_1, updRate=UPDATE_RATE_500):
        self.setNextOperation(REG_CLOCK, channel, 0)
        self.writeClockRegister(0, clkDivider, updRate)

        self.setNextOperation(REG_SETUP, channel, 0)
        self.writeSetupRegister(MODE_SELF_CAL, gain, polarity, 0, 0)

        while not self.dataReady(channel):
            pass

    def setNextOperation(self, reg, channel, readWrite):
        r = reg << 4 | readWrite << 3 | channel
        self.spi.xfer([r])

    # CLKDIS : master clock disable bit
    # CLKDIV : clock divider bit
    def writeClockRegister(self, CLKDIS, CLKDIV, outputUpdateRate):
        r = CLKDIS << 4 | CLKDIV << 3 | outputUpdateRate
        r &= ~(1 << 2)  # clear CLK
        self.spi.xfer([r])

    def writeSetupRegister(self, operationMode, gain, unipolar, buffered, fsync):
        r = operationMode << 6 | gain << 3 | unipolar << 2 | buffered << 1| fsync
        self.spi.xfer([r])

    def readADResult(self):
        b1 = self.spi.xfer([0x0])[0]
        b2 = self.spi.xfer([0x0])[0]
        r = int(b1 << 8 | b2)

        return r

    def readADResultRaw(self, channel):
        while not self.dataReady(channel):
            pass
        self.setNextOperation(REG_DATA, channel, 1)

        return self.readADResult()

    def readVoltage(self, channel, vref, factor=1):
        return float(self.readADResutlRaw(channel)) / 65536.0 * vref * factor

    def dataReady(self, channel):
        self.setNextOperation(REG_CMM, channel, 1)
        b1 = self.spi.xfer([0x0])[0]

        return (b1 & 0x80) == 0x0

    def reset(self):
        for i in range(100):
            self.spi.xfer([0xff])


fs = 44100
flag = 0

class Node:  # 받은 값을 저장하기 위한 링크드 리스트
    def __init__(self, count=None, fsif=None, time=None, next=None, prev=None):
        self.count = count
        self.fsif = fsif
        self.time = time
        self.next = next
        self.prev = prev

    def setting(self, tail):
        self.next = tail
        tail.prev = self

    def add_prev(self, count, fsif, time):
        temp = Node(count, fsif, time)
        temp.prev = self.prev
        temp.prev.next = temp
        temp.next = self
        self.prev = temp

    def add_list(self, head, tail):
        tail.next = self
        head.prev = self.prev
        self.prev.next = head
        self.prev = tail

    def remove_next(self):
        global flag
        head_next = self.next
        if head_next.fsif is None:
            return None, None, None

        count = head_next.count
        fsif = head_next.fsif
        time = head_next.time
        self.next = head_next.next
        head_next.next.prev = self
        del head_next

        return count, fsif, time


class zmq_handler(threading.Thread):
    def __init__(self, head, tail):
        threading.Thread.__init__(self)
        self.count = 0
        self.head = head
        self.tail = tail
        self.temp_head = Node()
        self.temp_tail = Node()
        self.temp_head.setting(self.temp_tail)

        pub_port = 8889
        context = zmq.Context()

        # zmq pub
        self.pub_socket = context.socket(zmq.PUB)
        self.pub_socket.bind("tcp://*:%s" % pub_port)


    def run(self):  # 2개의 라즈베리파이로 분업하기(주고받기) 위해 만들어놓은 함수
        global flag

        while True:
            string = self.sub_socket.recv()

            temp = np.fromstring(string, dtype=np.float)
            c = int(len(temp) / 883) #c 전체 데이터를 883으로 나누면 됨(c * 883 배열이므로)
            f = np.empty((c, 882)) #지금 1차원배열로 받으므로 나중에 처리해줘야함
            t = []
            for i in range(0, c):
                f[i] = temp[(i * 883):((i * 883) + 882)]
                t.append(temp[((i + 1) * 883) - 1])

            if flag is not 0:
                self.temp_tail.add_prev(c, f, t)
                self.count += 1
            else:
                flag = -1
                if self.count is not 0:
                    self.tail.add_list(self.temp_head.next, self.temp_tail.prev)
                    self.count = 0
                self.tail.add_prev(c, f, t)
                flag = 0

    def send(self, data, time):
        time = np.array2string(time)
        data = np.array2string(data[:, 0])
        result = time + data
        self.pub_socket.send_string(result)
        print(result)


class wav_handler:
    def __init__(self, file_name):
        self.fs, self.data = wavfile.read(file_name)
        self.data = self.data.T
        self.count = 0

    def get_chunk(self):
        if self.count + fs < self.data.shape[1]:
            data = self.data[:, self.count: self.count + fs]
            self.count += fs
            return data
        else:
            return None


class fft_handler:
    def __init__(self):
        self.opp = 0
        self.fs = fs
        self.Tp = 0.052
        self.n = int(self.Tp * self.fs);

    def dbv(self, input):
        return 20 * np.log10(abs(input))

    def get_line(self, raw):  # 사각파에서 증가부분을 찾는 함수
        self.leftarray = raw[0]
        self.rightarray = raw[1]
        self.start = (self.leftarray > 0) #주파수값이 증가하고 있는 지 판단함(양수면 증가)

    def data_process(self):
        spliter = 58  # let spliter=x, 1700/x + x/2 >= 2*(1700/2)^(1/2) = 58, when equals x = 58
        count = 0
        time = []
        fsif = np.zeros([100, self.n], dtype=np.float)

        for ii in range(11, int((self.start.shape[0] - self.n)), spliter):  # 개선된 탐색문
            if (ii - spliter > 0) & (self.start[ii] == True) & (self.start[ii - 11 - spliter:ii - spliter].max() == False):  # if start[ii] is true and the mean of from start[ii-11] to start[ii-1] is zero (All False)
                for jj in range(ii - spliter, ii):
                    if (self.start[jj] == True) & (self.start[jj - 11:jj - 1].mean() == 0.0):
                        fsif[count, :] = self.rightarray[jj:jj + self.n]  # then copy rightarray from ii to ii+n and paste them to sif[count] --> sif[count] is a list
                        time.append((jj + int(self.start.shape[0]) * self.opp) * 1. / self.fs)  # append time, the time is ii/fs --> few micro seconds (0.0001 sec or so)
                        count = count + 1

                        fsif[count, :] = self.rightarray[jj + 1:jj + 1 + self.n]  # then copy rightarray from ii to ii+n and paste them to sif[count] --> sif[count] is a list
                        time.append((jj + 1 + int(self.start.shape[0]) * self.opp) * 1. / self.fs)  # append time, the time is ii/fs --> few micro seconds (0.0001 sec or so)
                        count = count + 1

                        break

        self.opp += 1
        data_time = np.array(time)  # change the format of time from list to to np.array
        sif = fsif[:count, :]   # truncate sif --> remove all redundant array lists in sif, just in case if sif is longer then count
        sif = sif - np.tile(sif.mean(0), [sif.shape[0], 1]);
        zpad = int(8 * self.n / 2)  # create the number_of_ifft_entities --> which is the number of vales that has to be created from fft calculation
        v = self.dbv(np.fft.ifft(sif, zpad, 1))  # Do fft calculation, and convert results to decibel through dbv function
        s = v[:, 0:int(v.shape[1] / 2)]
        m = s.max()
        data_val = s - m
        data_time = data_time[:50]
        data_val = data_val[:50]

        return data_val, data_time


class max_handler:
    def __init__(self):
        self.n = 882
        self.lfm = [2535E6, 2556E6]  # e6 = * 10^6
        self.max_detect = 3E8 / (2 * (self.lfm[1] - self.lfm[0])) * self.n / 2
        self.y_len = 1764

        self.ignore_distance = 2.5
        self.ignore_index = int(self.ignore_distance * self.y_len / self.max_detect)

        self.data_time = []
        self.data_val = []
        self.data_tlen = 0
        self.data_vallen = 0

        self.time = []
        self.max_distance = []

        self.initial_time = -1
        self.initial_distance = -1
        self.min_initial_distance = 10
        self.front_val = []
        self.front_t = []

    def get_data(self, val, time):
        self.data_time = np.insert(time, len(time), 1.0)
        self.data_val = val
        self.data_tlen = len(self.data_time)
        self.data_vallen = len(self.data_val)

    def print_max(self):
        self.time = []
        self.max_distance = []
        for i in range(0, self.data_tlen - 1):
            self.time.append((self.data_time[i] + self.data_time[i + 1]) / 2)
            max_index = np.argmax(self.data_val[i][self.ignore_index:])
            self.max_distance.append(self.ignore_distance + max_index * self.max_detect / self.y_len)
        if (self.initial_time == -1 and self.initial_distance == -1):
            self.set_initial()

        return self.time, self.max_distance

    def set_initial(self):
        t = []
        val = []
        check = 0

        for i in range(0, self.data_tlen - 1):
            if (self.max_distance[i] > self.min_initial_distance):
                t.append(self.time[i])
                val.append(self.max_distance[i])
        long_val = np.array(self.front_val + val)

        if (len(long_val) > 10 and np.var(long_val) < 100):
            minimum = 100
            mean = np.mean(long_val)
            for i in range(0, len(long_val)):
                if abs(long_val[i] - mean) < minimum:
                    self.initial_time = (self.front_t + t)[i]
                    self.initial_distance = long_val[i]
                    minimum = abs(long_val[i] - mean)
                    check = 1

        self.front_val = val
        self.front_t = t


class kmf_handler:
    def __init__(self, time=[], distance=[], initial_time=-1, initial_distance=-1, wav_time=1, max_speed=3):
        self.time = time
        self.data_maxrange = distance
        self.initial_time = initial_time
        self.initial_distance = initial_distance
        self.initial_range = None
        self.wav_time = wav_time
        self.max_speed = max_speed
        self.time_range = np.linspace(0, wav_time, 50 * wav_time)
        self.temp_slice_index = 0

    def setting(self, time, distance, initial_time=-1, initial_distance=-1):
        self.time = time
        self.data_maxrange = distance
        self.initial_time = initial_time
        self.initial_distance = initial_distance

    def data_process(self):
        if self.initial_time is -1:  # 측정할 필요가 없으면 버림
            return None, None

        # check start point
        if self.initial_range is None:
            for i in range(0, len(self.time)):
                if self.time[i] == self.initial_time:
                    self.initial_range = i
                    self.time_range = self.time_range + int(self.time[0] / 1)
                    self.time_range_afterinitial = self.time_range[self.initial_range:]
                    data_maxrange_afterinitial = self.data_maxrange[self.initial_range:]
                    self.avg = self.initial_distance
                    break
        else:
            # cut before first point
            self.time_range = self.time_range + 1
            self.time_range_afterinitial = self.time_range
            data_maxrange_afterinitial = self.data_maxrange

        # seperate by time (1 second)
        afterinitial_noise = np.zeros(50)
        afterinitial_noise = data_maxrange_afterinitial[:]
        length = len(afterinitial_noise)

        # cut lower and upper value
        hap = 0
        hapcnt = 0
        for i in range(0, length):
            if ((self.avg - self.max_speed < afterinitial_noise[i]) and (afterinitial_noise[i] < self.avg + self.max_speed)):
                hap += afterinitial_noise[i]
                hapcnt += 1
            else:
                afterinitial_noise[i] = -1
        self.avg = hap / float(hapcnt)

        # fill -1 values
        first_val = 0
        last_val = 0
        check = 0
        if self.temp_slice_index != 0:  # 앞의 데이터에서 처리하지 못한 부분을 붙여줌
            afterinitial_noise = np.concatenate((self.temp_slice_data, afterinitial_noise), 0)
            self.time_range_afterinitial = np.concatenate((self.temp_slice_time, self.time_range_afterinitial), 0)
            self.temp_slice_index = 0
        if afterinitial_noise[0] < 0:   # 첫 값이 음수라면 이전 데이터의 마지막 값을 가져옴
            afterinitial_noise = np.insert(afterinitial_noise, 0, self.temp_last_data)
            check = 1
        length = len(afterinitial_noise)
        after_noise_cancel = np.zeros(length)
        after_noise_cancel[0] = afterinitial_noise[0]
        for i in range(1, length):  # 데이터의 노이즈를 제거  하는 과정
            after_noise_cancel[i] = afterinitial_noise[i]
            if after_noise_cancel[i] != -1.0:  # 음수 부분이 노이즈이므로 앞 뒤와 일정한 간격의 값으로 대체해줌
                first_val = last_val
                last_val = i
                self.temp_last_data = after_noise_cancel[last_val]
                gap = (after_noise_cancel[last_val] - after_noise_cancel[first_val]) / (last_val - first_val)
                for j in range(first_val + 1, last_val):
                    after_noise_cancel[j] = after_noise_cancel[j - 1] + gap
                continue
            if i == length - 1:  # 마지막이 음수면 처리가 안돼므로 저장한 뒤 다음 데이터와 함께 처리함
                self.temp_slice_index = last_val
                self.temp_slice_data = np.zeros(length - self.temp_slice_index + 1)
                if check == 0:
                    self.temp_slice_data = after_noise_cancel[self.temp_slice_index:]
                else:
                    self.temp_slice_data = after_noise_cancel[self.temp_slice_index + 1:]
                self.temp_slice_time = np.zeros(length - self.temp_slice_index + 1)
                self.temp_slice_time = self.time_range_afterinitial[self.temp_slice_index:]

        if self.temp_slice_index != 0:  # 시작이 음수일 때, 마지막이 음수일 때 등의 조건에 맞게 처리해줌
            if check == 0:
                return self.get_kmf(after_noise_cancel[:self.temp_slice_index + 1]), self.time_range_afterinitial[:self.temp_slice_index + 1]
            else:
                self.temp_slice_index = self.temp_slice_index - 1
                return self.get_kmf(after_noise_cancel[1:self.temp_slice_index + 2]), self.time_range_afterinitial[:self.temp_slice_index + 1]
        else:
            if check == 1:
                return self.get_kmf(after_noise_cancel[1:]), self.time_range_afterinitial
            else:
                return self.get_kmf(after_noise_cancel), self.time_range_afterinitial

    def get_kmf(self, after_noise_cancel):
        kf = KalmanFilter(transition_matrices=np.array([[1, 1], [0, 1]]), transition_covariance=([[0.25, 0], [0, 0]]), initial_state_mean=[29, -1.5])
        self.after_kf = kf.em(after_noise_cancel).smooth(after_noise_cancel)[0]

        return self.after_kf


def main():
    global flag

    spi = spi_handler()
    spi.initChannel(CHN_AIN1)

    while True:
        print(spi.readADResultRaw(CHN_AIN1))

    head = Node()
    tail = Node()
    head.setting(tail)
    zmq = zmq_handler(head, tail)
    wav = wav_handler("./wav/range_test2.wav")
    fft = fft_handler()
    max = max_handler()
    kmf = kmf_handler()

    temp = 0
    while True:
        # if flag is not 0:  # 공유자원을 사용하기 위한 플래그 코드
        #     continue
        # flag = 1
        # c, f, t = head.remove_next()
        # flag = 0
        # if c is None:
        #     continue

        raw = wav.get_chunk()
        if raw is None:
            break

        fft.get_line(raw)
        val, t = fft.data_process()
        max.get_data(val, t)
        t, distance = max.print_max()

        kmf.setting(t, distance, max.initial_time, max.initial_distance)
        send_data, send_time = kmf.data_process()

        if send_data is None:
            continue

        # 그래프 그리는 코드
        temp = temp + 1
        print(temp)
        pl.plot(send_time, send_data[:, 0])

        pl.xlim(0, 30)
        pl.ylim(-10, 70)

        pl.show()

        #zmq.send(send_data, send_time)


main()
