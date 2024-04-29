import time
from aggregator import aggregate
from MCFS.MCFS import MCFS
from match import get_report
from UTD import UTD

def main():
	start_time = time.time()
	aggregate()
	MCFS()
	# UTD()
	get_report()
	end_time = time.time()
	print(str(end_time - start_time) + " s")

if __name__ == '__main__':
	main()