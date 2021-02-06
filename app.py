import uvicorn
from fastapi import FastAPI, File, UploadFile
from process import face_similarity
import shutil
import os

def statusOK(data):
	print('Status: 200 OK')
	print('Content-Type: text/plain')
	print('')
	if data is not None:
		print(data)

#init app
app = FastAPI()
celeb_embed_path = ''
celeb2j_id_path = ''

if not os.path.exists('temp'):
	os.makedirs('temp')

@app.post("/post")
async def handler(uploaded_file: UploadFile = File(...)):
	file_location = f"temp/{uploaded_file.filename}"
	with open(file_location, "wb+") as image:
		shutil.copyfileobj(uploaded_file.file, image)

	img_path = file_location
	if img_path:
		result = face_similarity(img_path, celeb_embed_path, celeb2j_id_path)
		return statusOK(result)
		#return 'everythings fine'
	else:
		return 0
	

if __name__ == '__main__':
	uvicorn.run(app, port=9999)