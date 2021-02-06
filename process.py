#!pip install facenet-pytorch
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from torchvision import transforms
import torch
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

mtcnn = MTCNN(image_size=160, margin=30)
to_PIL = transforms.ToPILImage()
resize = transforms.Resize(160)
to_tensor = transforms.ToTensor()
resnet = InceptionResnetV1(pretrained='vggface2').eval()

def get_tensor(dframe, row_idx):
  z = torch.tensor(dframe.loc[row_idx, '0':]).unsqueeze(0)
  return z

#img_path or image
def face_similarity(img_path, celeb_embed_path, celeb2j_id_path):
  df = pd.read_csv(celeb_embed_path)
  df1 = pd.read_csv(celeb2j_id_path)
  try:
    # путь если нужно
    image = Image.open(img_path)

    # (убрать ресайз)
    image = mtcnn(resize(image))
    
    embedding = resnet(image.unsqueeze(0)).detach()
    max = -1
    argmax = -1
    for i in range(len(df)):
      if cosine_similarity(embedding, get_tensor(df, i)) > max:
        max = cosine_similarity(embedding, get_tensor(df, i))[0][0]
        argmax = i

    name = df.loc[argmax, 'Person_name']
    jewel_id_list = list(df1[name].loc[2:5, ])
    result = jewel_id_list[0] + ', ' + jewel_id_list[1] + ', ' + jewel_id_list[2]
    return result
  except:
    return 'Recognition error'
