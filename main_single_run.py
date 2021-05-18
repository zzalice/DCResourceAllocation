from src.simulation.iteration import OneIterationAlgo

if __name__ == '__main__':
    folder_data: str = '0513-010046L_'
    folder_topic: str = '3layer'
    file_iter: int = 33
    algorithm: str = 'DC-RA'  # 'DC-RA', 'FRSA', 'MSEMA', 'Baseline'
    OneIterationAlgo(folder_data, folder_topic, file_iter, algorithm).run()
