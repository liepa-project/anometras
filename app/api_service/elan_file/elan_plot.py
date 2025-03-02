import io
#import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from pyannote.core import Annotation, Segment
from pyannote.core import notebook

notebook.width = 10
plt.rcParams['figure.figsize'] = (notebook.width, 3)




async def plot_segments(annotation: Annotation) -> io.BytesIO:
    # annotation = Annotation()
    # annotation[Segment(2, 5)] = 'A'
    # annotation[Segment(4, 8)] = 'B'
    # annotation[Segment(9, 10)] = 'A'

    # notebook.crop = Segment(0, 10)

    figure, ax = plt.subplots()
    plt.figure().set_figwidth(15)
    # print(annotation)
    # notebook.crop = Segment(250, 500)

    notebook.plot_annotation(annotation, ax=ax, time=True, legend=True)



    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close(figure)
    return img_buf

