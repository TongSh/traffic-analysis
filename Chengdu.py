# -*- coding: utf-8 -*-
from math import *
import matplotlib.pyplot as plt
import numpy as np
import os
import os.path
import time
#from list import *
from test import *
import sys

#平面上求两点相对方向
#完全当作平面几何进行求解
#只适合两点距离很近的时候（小于1KM）
def calAngle(aLa,aLo,bLa,bLo):
	angle = 0
	if bLa == aLa and bLo == aLo:
		angle = -100
		return angle
	#维度相等
	elif bLa == aLa:
		if bLo > aLo:
			angle = 90
		else:
			angle = 270
		return angle
	elif bLo == aLo:
		if bLa > aLa:
			angle = 0
		else:
			angle = 180
	else:
		angle = atan((bLo-aLo)*cos(bLa*pi/180)/(bLa-aLa))
		angle = angle * 180/pi
		if aLa<bLa and aLo<bLo:
			return angle
		elif aLa<bLa and aLo>bLo:
			angle = angle + 360
		else:
			angle = 180 + angle
	return angle

#极坐标法
#思路就是将地球放在一个球坐标系中并适当调整三个参数的起始点以减少后面的运算量，
#然后将各点由球坐标转化为直角坐标，
#之后依据平面法向量的定理求得二面夹角也就是航向，
#之后转化为符合航向定义的度数。
def calAngle2(lat1,lon1,lat2,lon2):
	dlat = lat2 - lat1
	dlon = lon2 - lon1
	y = sin(dlon*pi/180)*cos(lat2*pi/180)
	x = cos(lat1*pi/180)*sin(lat2*pi/180)-sin(lat1*pi/180)*cos(lat2*pi/180)*cos(dlon*pi/180)
	if y > 0:
		if x > 0:
			tc1 = atan(y/x)
		if x < 0:
			tc1 = pi - atan(-y/x)
	   	if x == 0:
	   		tc1 = pi/2
	if y < 0:
		if x > 0:
			tc1 = -atan(-y/x)
	   	if x < 0:
	   		tc1 = atan(y/x)-pi
	   	if x == 0:
	   		tc1 = -1*pi/2
	if y == 0:
		if x > 0:
			tc1 = 0
	   	if x < 0:
	   		tc1 = pi
	   	if x == 0:
	   		tc1 = -1
	return tc1/pi*180

#创建文件夹
def mkdir(path):
	# 去除首位空格
	path = path.strip()
	# 去除尾部 \ 符号
	path = path.rstrip("\\")
	# 判断路径是否存在
	# 存在     True
	# 不存在   False
	isExists = os.path.exists(path)
	# 判断结果
	if not isExists:
		# 如果不存在则创建目录
		# 创建目录操作函数
		os.makedirs(path)
		print path + ' 创建成功'
		return True
	else:
		# 如果目录存在则不创建，并提示目录已存在
		print path + ' 目录已存在'
		return False

# 计算两个角度的夹角
def deltaAngle(angle1, angle2):
	r1 = abs(angle2 - angle1)
	if r1 < (360 - r1):
		return r1
	else:
		return 360 - r1

#输入两点经纬度，输出距离（单位：米）
def distance(position1,position2):
	a = position1[1] - position2[1]
	b = position1[0] - position2[0]
	distance = 2*asin(sqrt(sin(a/2)*sin(a/2)+cos(position1[1])*cos(position2[1])*sin(b/2)*sin(b/2)))*6378.13
	return distance

#样本数据集包含10000+辆成都出租车的行驶轨迹记录，每两次采样的时间间隔约为10~15sec
def findDirection():
	# 依次读各个文件
	#写出文件夹
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'VNDN' + s + 'Chengdu'
	out1 = root + s + 'direction result 60sec'
	mkdir(out1)
	# out2 = root + s + 'stop track'
	# mkdir(out2)
	data_sourse = root + s + '60sec_taxi_log_2008_by_id'
	list = os.listdir(data_sourse)  # 列出目录下的所有文件
	for line in list:
		filename2 = data_sourse + s + line
		print filename2
		try:
			f_r = open(filename2, 'r')
		except IOError:
			continue

		# 行驶方向结果写出
		w_filename2 = out1 + s + line.split('.')[0] + '.csv'
		try:
			f_w = open(w_filename2, 'w')
		except IOError:
			continue
		line_before = f_r.readline()  # 第一行不能主动跟别人比对
		line_now = f_r.readline()#line_now可以跟line_before比对
		count = 1
		state = 'stop'
		if line_before:#排除空文件第一行为空的危险
			state_start_time = int(line_before.split(',')[3].split('.')[0])
			state_start_position = [line_before.split(',')[2],line_before.split(',')[1]]
		state_end_time = 0.0
		#用来判断停车时间是否构成5min
		judge_stop = False
		judge_stop_start_time = 0.0
		#用来判断运动时间是否达到5min
		judge_move = False
		judge_move_start_time = 0.0
		judge_move_start_position = [0.0, 0.0]
		move_pending_array = []
		stop_pending_array = []
		while line_now:
			#首先读取当前时刻和上一时刻的数据
			try:
				lon_now,lat_now,time_now = float(line_now.split(',')[2]),float(line_now.split(',')[1]),int(line_now.split(',')[3].split('.')[0])
			except ValueError:
				continue
			try:
				lon_before,lat_before,time_before = float(line_before.split(',')[2]),float(line_before.split(',')[1]),int(line_before.split(',')[3].split('.')[0])
			except ValueError:
				continue
			dis = distance([lon_now,lat_now],[lon_before,lat_before])

			# 特别处理时间间隔大于3600的情况
			if abs(time_now - time_before) > 3600:
				if state == 'stop':
					if judge_move:  # 这时需要把这些记录当作停止记录写出去
						judge_move = False  # 初始化运动状态切换到静止态的判断条件
						# 写出列表里的待写出项（历史项）
						for str_item in move_pending_array:
							rec = str_item.split(',')
							w_str = '-1,stop,' + rec[2] + ',' + rec[3] + ',' + rec[4] + ',' + rec[5]
							f_w.write(w_str)
						move_pending_array = []  # 写出后，清空数组
					# 输出现在的这条stop记录
					w_str = '-1,stop,' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) + ',' + str(dis) + '\n'
					f_w.write(w_str)
					judge_move = False
				else:
					if judge_stop:  # 需要把待定stop的记录变成真的stop
						for str_item in stop_pending_array:
							rec = str_item.split(',')
							w_str = str(-1) + ',stop,' + rec[2] + ',' + rec[3] + ',' + rec[4] + ',' + rec[5]
							f_w.write(w_str)
						stop_pending_array = []  # 写出后，清空数组
						state = 'stop'  # 将状态切换到stop状态
						# try:
						# 	state_start_time = int(stop_pending_array[0].split(',')[2])
						# 	state_start_position = [int(stop_pending_array[0].split(',')[3]),int(stop_pending_array[0].split(',')[4])]
						# except ValueError:
						# 	print ValueError
						judge_move = False
					else:  # 否则将当前这条（3600后的第一条）作为stop处理
						# 输出现在的这条stop记录
						w_str = str(-1) + ',stop,' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) + ',' + str(dis) + '\n'
						f_w.write(w_str)
						state = 'stop'  # 将状态切换到stop状态
						# state_start_time = int(time_now)
						# state_start_position = [lon_now,lat_now]
						judge_move = False
				line_before = line_now
				line_now = f_r.readline()  # 读新行
				continue

			if state == 'stop':#如果当前是停止状态
				if distance([lon_now,lat_now],[lon_before,lat_before]) < 10:#当前这条相对于上条记录是停止
					if judge_move:#倘若之前是在一个move待定周期
						# 这个待定周期作废了，待定周期里面的运动记录不输出
						# 清空待写出列表
						judge_move = False
						move_pending_array = []
					#输出现在的这条stop记录
					w_str = str(-1) + ',stop,' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
					f_w.write(w_str)
				else:#这条记录相比于上一条是运动了的，检查是不是在运动待定周期
					if judge_move:#在一个move检查周期内（检查move有没有达到1min）
						if (time_now - judge_move_start_time) > 60 :
							state = 'move'#切换到运动状态

							#输出stop持续时间
							# w_filename3 = out2 + s + line.split('.')[0] + '.csv'
							# try:
							# 	f_w_stop = open(w_filename3, 'a')
							# except IOError:
							# 	continue
							# f_w_stop.write(str(state_start_time)+','+str(move_pending_array[0].split(',')[2])+',')
							# f_w_stop.write(str(state_start_position[0])+','+str(state_start_position[1])+',')
							# f_w_stop.write(move_pending_array[0].split(',')[3]+','+ move_pending_array[0].split(',')[4]+',')
							# f_w_stop.write(str(distance([float(state_start_position[0]),float(state_start_position[1])],[float(move_pending_array[0].split(',')[3]),float(move_pending_array[0].split(',')[4])]))+'\n')

							judge_stop = False#初始化运动状态切换到静止态的判断条件
							#写出列表里的待写出项（历史项）
							for str_item in move_pending_array:
								f_w.write(str_item)
								count += 1
							move_pending_array = []#写出后，清空数组
							#当前的这条记录也要写出去
							angle = calAngle(lat_before, lon_before,lat_now, lon_now)
							w_str = str(count) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
							f_w.write(w_str)
							count += 1
						else:
							#虽然在运动，但还没满足状态条件，先写到列表里
							angle = calAngle(lat_before, lon_before,lat_now, lon_now)
							w_str = str(count + len(move_pending_array)) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
							move_pending_array.append(w_str)
					else:#开启一个move待定周期，记录待定周期的开始时间
						judge_move = True
						judge_move_start_time = time_now
						#先写到列表里
						angle = calAngle(lat_before, lon_before,lat_now, lon_now)
						w_str = str(count + len(move_pending_array)) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) + ','+str(dis) + '\n'
						move_pending_array.append(w_str)
			else:#当前是运动周期
				if distance([lon_now,lat_now],[lon_before,lat_before]) >= 10:#且当前这条记录相较于上条也运动，保持运动状态，写出
					if judge_stop:
						# 这个stop待定周期作废了
						judge_stop = False
						#把这个待定周期里面的记录写出去
						for str_item in stop_pending_array:
							rec = str_item.split(',')
							w_str = rec[0] + ',' + rec[1] + ',' + rec[2] + ',' + rec[3] + ',' + rec[4] + ',' + rec[5].split('\n')[0]+',pending stop\n'
							f_w.write(w_str)
							count += 1
						stop_pending_array = []
					#写出当前这条运动记录
					angle = calAngle(lat_before, lon_before,lat_now, lon_now)
					w_str = str(count) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
					f_w.write(w_str)
					count += 1
				else:#这条记录相比于上一条是静止的，检查是否在静止待定周期
					if judge_stop:#在一个stop检查周期内（检查stop有没有达到10min）
						if (time_now - judge_stop_start_time) > 600:
							judge_move = False
							state = 'stop'
							#记录stop开始时间和坐标
							# try:
							# 	state_start_time = int(stop_pending_array[0].split(',')[2])
							# 	state_start_position = [float(stop_pending_array[0].split(',')[3]),float(stop_pending_array[0].split(',')[4])]
							# except ValueError:
							# 	print ValueError,'in stop'
							# 写出列表里的待写出项（这些项不能算到trip里，所以把其方向改为stop)
							for str_item in stop_pending_array:
								rec = str_item.split(',')
								w_str = str(-1) + ',stop,' + rec[2] + ',' + rec[3] + ',' + rec[4] + ',' + rec[5]
								f_w.write(w_str)
							stop_pending_array = []
							#输出当前这条记录
							w_str = str(-1) + ',stop,' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) +','+str(dis)+ '\n'
							f_w.write(w_str)
						else:
							#虽然静止，但还没满足状态条件，把待定静止的记录写到数组中
							angle = calAngle(lat_before, lon_before, lat_now, lon_now)
							w_str = str(count + len(stop_pending_array)) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) + ',' + str(dis) + '\n'
							stop_pending_array.append(w_str)
					else:#开启一个stop检查周期
						judge_stop = True
						judge_stop_start_time = time_now
						#把待定静止的记录写到数组中
						angle = calAngle(lat_before, lon_before, lat_now, lon_now)
						w_str = str(count + len(stop_pending_array)) + ',' + str(angle) + ',' + str(time_now) + ',' + str(lon_now) + ',' + str(lat_now) + ',' + str(dis) + '\n'
						stop_pending_array.append(w_str)
			line_before = line_now
			line_now = f_r.readline()  # 读新行
		f_r.close()
		f_w.close()

# 求出租车各段trip持续时间以及每段trip方向变化次数
def findTrip():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'VNDN' + s + 'Chengdu'
	dir_result = root + s + 'direction result 60sec\\'  # 车辆方向结果
	out = root + s + 'Trip Cruise\\'
	mkdir(out)
	out2 = root + s + 'stop track'
	mkdir(out2)
	list = os.listdir(dir_result)  # 列出目录下的所有文件
	for name in list:
		# 读初步统计结果（序号，行驶方向，时间）
		filename = dir_result + s + name
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		# 将每段trip写出成一个文件，一辆车的存在一个文件夹下面,文件夹以车编号命名
		trip_dir = out + s + name.split('.')[0]
		mkdir(trip_dir)

		# 写出Trip Cruise统计结果（trip序号，cruise序号，持续时间duration）
		# 下面这个f_w肯定会被close
		try:
			f_w = open(root + s + '1.csv', 'w')
		except IOError:
			continue

		line_org = f_r.readline()  # 首行,调用文件的 readline()方法
		# 初始状态，都认为不是处在一段trip中
		inTrip = False
		# trip的起止时间
		tripStartTime = 0
		tripEndTime = 0
		# cruise的起止时间
		cruiseStartTime = 0
		cruiseEndTime = 0
		# 序号
		tripNumber = 1
		cruiseNumber = 1
		# 方向角，用于cruise统计
		angle_now = 0.0
		angle_last = 0.0
		cruise_start_angle = 0.0
		cruise_average_angle = 0.0
		# 为求平均角度而用来计数
		count_for_average = 0



		if line_org:
			timeSec_old = int(line_org.split(',')[2].split('.')[0])
			lon_old = float(line_org.split(',')[3])
			lat_old = float(line_org.split(',')[4])
			# 记录stop漂移
			stop_start_time = timeSec_old
			stop_start_position = [lon_old, lat_old]
		f_w_stop = open(out2 + s + str(name), 'a')
		# 一行行读
		while line_org:
			line = line_org.split(',')
			count = int(line[0])
			direction = line[1]  # 有可能是stop
			timeSec = int(line[2].split('.')[0])
			lon = float(line[3])
			lat = float(line[4])
			# 读新行
			line_org = f_r.readline()
			if inTrip:
				if count != -1:  # cruise还没结束
					dir = float(direction)
					tripEndTime = timeSec  # 不断更新的结束时间，直到真正结束
					# 统计方向变化
					angle_now = dir
					# cruise终止条件
					if deltaAngle(angle_now, angle_last) > 15 or deltaAngle(angle_now,cruise_start_angle) > 45 or deltaAngle(
							angle_now, cruise_average_angle) > 30:
						# 一段cruise结束了
						if cruiseEndTime - cruiseStartTime > 0:  # 除去单记录
							str_w = str(tripNumber) + ',' + str(cruiseNumber) + ',' + str(
								cruiseEndTime - cruiseStartTime) + ',' + str(cruise_average_angle) + ',' + str(
								cruise_start_angle) + ',' + str(cruiseStartTime) + ',' + str(cruiseEndTime) + '\n'
							f_w.write(str_w)
							cruiseNumber = cruiseNumber + 1
						# 重新开始一段cruise
						angle_last = angle_now
						cruise_start_angle = angle_now  # 一段cruise开始时候的方向角
						cruise_average_angle = angle_now  # 初始平均值
						count_for_average = 1
						cruiseStartTime = timeSec
					# 否则，cruise没有结束，更新cruise_average_angle
					else:
						# 角度平均值
						angle_array = [cruise_average_angle] * count_for_average
						angle_array.append(angle_now)
						cruise_average_angle = angle_avg(angle_array, count_for_average + 1)
						count_for_average += 1
						cruiseEndTime = timeSec  # 实时更新的
						angle_last = angle_now
				else:  # 遇到了stop
					stop_start_time = timeSec
					stop_start_position = [lon,lat]
					# tripEndTime由前面不断更新得到，现在应该是最后一条运动记录的时刻
					inTrip = False
					duration = tripEndTime - tripStartTime
					if duration <= 0:  # 一条记录的情况，不要
						# 接下来重新开始一段trip,trip标号不变化
						cruiseNumber = 1
						timeSec_old = timeSec
						continue
					# print 'duration ',duration,' tripStartTime ',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tripStartTime)),' tripEndTime ',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tripEndTime))
					# 这也意味着一段cruise结束了。输出这段cruise的持续时间
					cruiseEndTime = tripEndTime  # 一段cruise结束了
					# 排除只有一条记录的cruise
					if cruiseEndTime - cruiseStartTime > 0:
						str_w = str(tripNumber) + ',' + str(cruiseNumber) + ',' + str(cruiseEndTime - cruiseStartTime) + ',' + str(cruise_average_angle) + ',' + str(cruise_start_angle) + ',' + str(cruiseStartTime) + ',' + str(cruiseEndTime) + '\n'
						f_w.write(str_w)
					# 接下来重新开始一段trip
					tripNumber = tripNumber + 1
					cruiseNumber = 1
			else:
				if count != -1:
					dir = float(direction)
					inTrip = True  # 一段trip开始了
					f_w_stop.close()
					try:
						f_w_stop = open(out2 + s + str(name), 'a')
					except IOError:
						print IOError
						timeSec_old = timeSec
						lon_old = lon
						lat_old = lat
						continue
					f_w_stop.write(str(stop_start_time) + ',' + str(stop_start_position[0]) + ',' + str(stop_start_position[1]) + ',')
					f_w_stop.write(str(timeSec_old) + ',' + str(lon_old) + ',' + str(lat_old) + ',')
					f_w_stop.write(str(distance([float(stop_start_position[0]),float(stop_start_position[1])],[float(lon_old),float(lat_old)]))+'\n')


					# 准备写一个新的文件
					f_w.close()  # 先关闭旧的
					try:
						f_w = open(trip_dir + s + str(tripNumber) + '.csv', 'w')
					except IOError:
						timeSec_old = timeSec
						lon_old = lon
						lat_old = lat
						continue
					tripStartTime = timeSec
					cruiseStartTime = timeSec  # 一段trip的开始也意味着一段cruise的开始
					angle_now = dir  # cruise的起始方向
					angle_last = angle_now
					cruise_start_angle = dir  # 一段cruise开始时候的方向角
					cruise_average_angle = dir
					count_for_average = 1
					tripEndTime = timeSec  # 不断更新的结束时间，直到真正结束
				else:
					timeSec_old = timeSec
					lon_old = lon
					lat_old = lat
					continue  # 保持静止
			timeSec_old = timeSec
			lon_old = lon
			lat_old = lat
		# 文件末尾，意味着一段trip的结束
		# tripEndTime由前面不断更新得到，现在应该是最后一条运动记录的时刻
		inTrip = False
		duration = tripEndTime - tripStartTime
		if duration <= 0:  # 一条记录的情况，不要
			# 接下来重新开始一段trip,trip标号不变化
			cruiseNumber = 1
		# print 'duration ',duration,' tripStartTime ',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tripStartTime)),' tripEndTime ',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(tripEndTime))
		# 这也意味着一段cruise结束了。输出这段cruise的持续时间
		cruiseEndTime = tripEndTime  # 一段cruise结束了
		# 排除只有一条记录的cruise
		if cruiseEndTime - cruiseStartTime > 0:
			str_w = str(tripNumber) + ',' + str(cruiseNumber) + ',' + str(
				cruiseEndTime - cruiseStartTime) + ',' + str(cruise_average_angle) + ',' + str(
				cruise_start_angle) + ',' + str(cruiseStartTime) + ',' + str(cruiseEndTime) + '\n'
			f_w.write(str_w)
		# 接下来重新开始一段trip
		tripNumber = tripNumber + 1
		cruiseNumber = 1
		f_r.close()
		f_w.close()
findTrip()
# 遍历findTrip中输出的各个trip文件，选择其中长度大于60s的，生成trip&cruise统计（每车一个文件）
def findLongTrip():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'VNDN' + s + 'Chengdu'
	trip_dir = root + s + 'Trip Cruise'
	out = root + s + ' Long Trip Cruise'
	mkdir(out)
	list = os.listdir(trip_dir)  # 列出目录下的所有文件
	for num in list:
		# 读初步统计结果（序号，行驶方向，时间）
		dir_name = trip_dir + s + num
		list2 = os.listdir(dir_name)
		tripNumber = 1  # 记录最终要的trip编号
		# 挨个读取trip文件，根据trip时间，少于60s的剔除
		for m_trip in list2:
			trip_time = 0
			try:
				f_r = open(dir_name + s + m_trip, 'r')
			except IOError:
				continue
			line_org = f_r.readline()  # 首行,调用文件的 readline()方法
			while line_org:
				print 'a' + line_org
				line = line_org.split(',')
				timeSec = int(line[2])  # trip中一个cruise时间片
				trip_time += timeSec
				line_org = f_r.readline()
			if trip_time < 0:
				continue  # 淘汰持续时间少于60s的trip
			# 否则要将这段trip写到统计文件中
			try:
				f_w = open(out + s + num + '.csv', 'a')
			except IOError:
				continue
			# 为了写而重新读取
			f_r.close()
			try:
				f_r = open(dir_name + s + m_trip, 'r')
			except IOError:
				continue
			line_org = f_r.readline()  # 首行,调用文件的 readline()方法
			while line_org:
				print 'b' + line_org
				line = line_org.split(',')
				line[0] = str(tripNumber)  # 修改trip编号
				f_w.write(
					line[0] + ',' + line[1] + ',' + line[2] + ',' + line[3] + ',' + line[4] + ',' + line[5] + ',' +
					line[6])
				line_org = f_r.readline()
			tripNumber += 1
			f_w.close()
			f_r.close()


#统计行驶方向的分布情况
def dirDistribution():
	s = os.sep  # 根据unix或win，s为\或/
	#每10度一组，统计各个组别的记录条数
	means_dir = []
	for i in range(0,37):
		means_dir.append(0)
	root = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'direction result'
	list = os.listdir(root)  # 列出目录下的所有文件
	for line in list:
		#读初步统计结果（序号，行驶方向，时间）
		filename = root + s + line
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		print filename
		line_org = f_r.readline()  # 首行,调用文件的 readline()方法
		#一行行读
		while line_org:
			line = line_org.split(',')
			if int(line[0]) == -1:
				line_org = f_r.readline()  # 读新行
				continue
			dir = float(line[1])
			#print "dir=",dir,'   index=',(dir+180)/10
			means_dir[int((dir+180)/10)] = means_dir[int((dir+180)/10)]+1
			line_org = f_r.readline()  # 读新行
		f_r.close()

	# 统计结果写出
	w_filename2 = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'angle_result.csv'
	try:
		f_w = open(w_filename2, 'w')
	except IOError:
		print IOError
	c = 0
	for i in range(-170,190,10):
		str_f = str(i)+','+str(means_dir[c])+'\n'
		print str_f
		f_w.write(str_f)
		c = c + 1
	f_w.close()

#统计trip和crise的平均持续时间
def average():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'datasets' + s + 'NewChengdu'
	tc_result = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'Trip Cruise'  # 车辆trip和cruise结果
	#定义全局的变量：平均trip，平均cruise，trip计数，cruise计数
	trip_average = 0.0
	cruise_average = 0.0
	trip_count = 0
	cruise_count = 0
	trip_flag = 1#标记一辆车的不同trip
	trip_last_time = 0#trip持续的时间
	list = os.listdir(tc_result)  # 列出目录下的所有文件
	for line in list:
		#print line
		trip_flag = 1#当前文件的trip计数，每辆车（每个文件的trip都是从1开始编号）
		trip_last_time = 0#每个文件都要初始化trip持续时间为0
		#读tc统计结果
		filename = tc_result + s + line
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		print filename
		line_org = f_r.readline()  # 首行,调用文件的 readline()方法
		# 一行行读
		while line_org:
			line = line_org.split(',')
			if(trip_flag != int(line[0])):
				trip_average = (trip_average * trip_count + trip_last_time)/(trip_count + 1)#结束了一段trip，更新平均trip时间
				trip_count = trip_count + 1  # 更新trip计数
				trip_flag = trip_flag + 1#更新当前文件的trip计数
				trip_last_time = 0# trip持续时间归零
			cruise_time = int(line[2])#这段cruise的持续时间
			if cruise_time > 600:
				#print filename
				#print cruise_time
				trip_last_time = trip_last_time + cruise_time#增加trip持续时间
				line_org = f_r.readline()  # 读新行
				continue
			cruise_average = (cruise_average * cruise_count + cruise_time)/(cruise_count + 1)#更新平均时间
			#print 'cruise_average = ', cruise_average,' cruise_count = ',cruise_count,' cruise_time = ',cruise_time
			cruise_count = cruise_count + 1  # 每一行都是一段cruise，每一行都要更新cruise的计数
			trip_last_time = trip_last_time + cruise_time#增加trip持续时间
			line_org = f_r.readline()  # 读新行
		#文件读完，意味着最后一段trip结束
		trip_average = (trip_average * trip_count + trip_last_time) / (trip_count + 1)  # 结束了一段trip，更新平均trip时间
		trip_count = trip_count + 1  # 更新trip计数
		f_r.close()
	print 'trip_average',trip_average
	print 'trip_count',trip_count
	print 'cruise_average',cruise_average
	print 'cruise_count',cruise_count

#直观展示怎么切割trip和cruise
def showTrip():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'VNDN' + s + 'Chengdu'
	datasourse = r'E:' + s + 'VNDN' + s + 'Chengdu' + s + 'direction result 60sec'  # 车辆方向结果
	mkdir(root + s + 'SHOW\\')
	list = os.listdir(datasourse)  # 列出目录下的所有文件
	for line in list:
		#读初步统计结果（序号，行驶方向，时间）
		filename = datasourse + s + line
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		#写出Trip Cruise切割结果
		w_filename2 = root + s + 'SHOW' + s + line
		try:
			f_w = open(w_filename2, 'w')
		except IOError:
			continue
		line_new = f_r.readline()  # 首行,调用文件的 readline()方法
		line_old = line_new
		#初始状态，都认为不是处在一段trip中
		inTrip = False
		#trip的起止时间
		tripStartTime = 0
		tripEndTime = 0
		#cruise的起止时间
		cruiseStartTime = 0
		cruiseEndTime = 0
		#序号
		tripNumber = 1
		cruiseNumber = 1
		#方向角，用于cruise统计
		angle_now = 0.0
		angle_last = 0.0
		cruise_start_angle = 0.0
		cruise_average_angle = 0.0
		#为求平均角度而用来计数
		count_for_average = 0
		if line_new:
			timeSec = int((line_new.split(',')[2]).split('.')[0])  # 初始时间
		#一行行读
		while line_new:
			line = line_new.split(',')
			count = int(line[0])
			direction = line[1]#有可能是stop
			timeSec_old = timeSec
			timeSec = int(line[2].split('.')[0])
			#读新行,保存旧行（因为还没有写出去）
			line_old = line_new
			line_new = f_r.readline()
			if inTrip:
				if count != -1 and (timeSec - timeSec_old) < 3600:#cruise还没结束
					dir = float(direction)
					if dir == -100:#pending stop里面有两点完全重合情况，此时dir == -100
						continue
					tripEndTime = timeSec#不断更新的结束时间，直到真正结束
					#统计方向变化
					angle_now = dir
					#cruise终止条件
					if deltaAngle(angle_now,angle_last) > 15 or deltaAngle(angle_now,cruise_start_angle) > 45 or deltaAngle(angle_now,cruise_average_angle) > 30:
						#一段cruise结束了
						# if cruiseEndTime - cruiseStartTime > 0:  # 正常结束
						# 	f_w.write('##################################################### cruise END \n')
						# 	#f_w.write('注：'+','+str(angle_last) + ',' + str(cruise_start_angle) + ',' + str(cruise_average_angle) + '\n')
						# 	f_w.write('################################################### cruise START \n')
						# 	cruiseNumber += 1
						# else:
						# 	f_w.write('#################################################### cruise DROP \n')
						# 	#f_w.write('注：'+','+str(angle_last) + ',' + str(cruise_start_angle) + ',' + str(cruise_average_angle) + '\n')
						# 	f_w.write('################################################### cruise START \n')
						f_w.write(line_old)#终止条件是由line_old的内容引发，line_old不应该算到cruise里面来
						#重新开始一段cruise
						angle_last = angle_now
						cruise_start_angle = angle_now#一段cruise开始时候的方向角
						cruise_average_angle = angle_now#初始平均值
						count_for_average = 1
						cruiseStartTime = timeSec
					else:
						# 否则，更新cruise_average_angle
						angle_last = angle_now
						f_w.write(line_old)
						angle_array = [cruise_average_angle] * count_for_average
						angle_array.append(angle_now)
						cruise_average_angle = angle_avg(angle_array, count_for_average + 1)
						count_for_average += 1
						cruiseEndTime = timeSec#实时更新的
				else:#遇到了stop
					# 首先先考虑，这意味着一段cruise结束了。
					cruiseEndTime = tripEndTime
					# 排除只有一条记录的cruise
					# if cruiseEndTime - cruiseStartTime > 0:#正常结束
					# 	f_w.write('##################################################### cruise END \n')
					# else:
					# 	f_w.write('#################################################### cruise DROP \n')
					#f_w.write('注：'+','+str(angle_last) + ',' + str(cruise_start_angle) + ',' + str(cruise_average_angle) + '\n')
					#接下来考虑trip
					#tripEndTime由前面不断更新得到，现在应该是最后一条运动记录的时刻
					inTrip = False
					duration = tripEndTime - tripStartTime
					if duration < 0:#小于60s记录的情况，不要
						# 接下来重新开始一段trip,trip标号不变化
						f_w.write('======================================================== trip DROP \n')
						f_w.write(line_old)#这行stop写在标记后
						cruiseNumber = 1#由于被抛弃，trip编号不改变
					else:
						f_w.write('========================================================= trip END \n')
						f_w.write(line_old)  # 这行stop写在标记后
						tripNumber = tripNumber + 1#接下来重新开始一段trip
						cruiseNumber = 1

			else:
				if count != -1:
					dir = float(direction)
					inTrip = True#一段trip开始了
					f_w.write('======================================================= trip START \n')
					#f_w.write('################################################### cruise START \n')
					f_w.write(line_old)
					tripStartTime = timeSec
					cruiseStartTime = timeSec#一段trip的开始也意味着一段cruise的开始
					angle_now = dir#cruise的起始方向
					angle_last = angle_now
					cruise_start_angle = dir  # 一段cruise开始时候的方向角
					cruise_average_angle = dir
					count_for_average = 1
					tripEndTime = timeSec  # 不断更新的结束时间，直到真正结束
				else:
					#f_w.write(line_old)
					continue#保持静止，就不一直写出stop了

		# 首先先考虑，这意味着一段cruise结束了。
		cruiseEndTime = tripEndTime
		# 排除只有一条记录的cruise
		# if cruiseEndTime - cruiseStartTime > 0:  # 正常结束
		# 	f_w.write('##################################################### cruise END \n')
		# else:
		# 	f_w.write('#################################################### cruise DROP \n')
		# f_w.write('注：'+','+str(angle_last) + ',' + str(cruise_start_angle) + ',' + str(cruise_average_angle) + '\n')
		# 接下来考虑trip
		# tripEndTime由前面不断更新得到，现在应该是最后一条运动记录的时刻
		inTrip = False
		duration = tripEndTime - tripStartTime
		if duration < 0:  # 小于60s记录的情况，不要
			# 接下来重新开始一段trip,trip标号不变化
			f_w.write(line_old)  # 这行stop写在标记后
			f_w.write('======================================================== trip DROP \n')
			cruiseNumber = 1  # 由于被抛弃，trip编号不改变
		else:
			f_w.write(line_old)  # 这行stop写在标记后
			f_w.write('========================================================= trip END \n')
			tripNumber = tripNumber + 1  # 接下来重新开始一段trip
			cruiseNumber = 1
		f_r.close()
		f_w.close()

#首先筛选出满足时间间隔是否符合规范（60sec以内）的数据源文件
def washData():
	s = os.sep  # 根据unix或win，s为\或/
	root = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'cabspottingdata'
	out = r'E:'+s+'VNDN'+s+'Chengdu'+s+'60sec_taxi_log_2008_by_id'
	mkdir(out)
	for i in range(1, 7000):
		filename = root + s + str(i) + '.csv'
		try:
			print filename
			f_r = open(filename, 'r')
		except IOError:
			print IOError
			continue
		# 先检查
		# 不符合规范就淘汰这个文件
		line_org = f_r.readline()  # 首行title 调用文件的 readline()方法
		count = 0
		average_gap_time = 0.0
		# 一行行读
		while line_org:
			line = line_org.split(',')
			# 时刻1
			time1 = int(line[3].split('.')[0])
			line_org = f_r.readline()  # 读新行
			# 如果新行已经是文件尾，跳出
			if not line_org:
				break
			line = line_org.split(',')
			# 时刻2
			time2 = int(line[3].split('.')[0])
			gap_time = abs(time2 - time1)
			if gap_time == 0 or gap_time > 3600:
				continue#排除掉同一时刻输出两条记录
			average_gap_time = (average_gap_time * count + gap_time) / (count + 1)
			count += 1
		print average_gap_time
		if average_gap_time > 15:
			f_r.close()
			continue  # 淘汰这个文件
		#否则把这个文件倒腾出来
		f_r.close()
		try:
			m_w = open(out + s +str(i) + '.csv', 'w')
		except IOError:
			continue
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		line_org = f_r.readline()  # 首行title 调用文件的 readline()方法
		# 一行行读
		while line_org:
			m_w.write(line_org)
			line_org = f_r.readline()  # 读新行



#统计cruise时间的分布情况
def cruise():
	s = os.sep  # 根据unix或win，s为\或/
	#每10度一组，统计各个组别的记录条数
	cruise_time = [0]*1000
	root = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'Trip Cruise'
	list = os.listdir(root)  # 列出目录下的所有文件
	for line in list:
		#读初步统计结果（序号，行驶方向，时间）
		filename = root + s + line
		try:
			f_r = open(filename, 'r')
		except IOError:
			continue
		print filename
		line_org = f_r.readline()  # 首行,调用文件的 readline()方法
		#一行行读
		while line_org:
			line = line_org.split(',')
			cruise = int(line[2])
			if cruise < 1000 and cruise >= 0:
				cruise_time[cruise] += 1
			line_org = f_r.readline()  # 读新行
		f_r.close()

	# 统计结果写出
	w_filename2 = r'E:' + s + 'datasets' + s + 'NewChengdu' + s + 'cruise_result.csv'
	try:
		f_w = open(w_filename2, 'w')
	except IOError:
		print IOError

	for i in range(0,1000):
		str_f = str(i)+','+str(cruise_time[i])+'\n'
		print str_f
		f_w.write(str_f)
	f_w.close()
