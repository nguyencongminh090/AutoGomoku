from utils import *
import cv2


img = cv2.imread('Screenshot_2.png')
detect = detect_board(img, rectangle=False)
new_img = img_crop(img, detect[0], detect[1], detect[3], detect[2])
print(detect)
cv2.imshow('img', img)
cv2.imshow('new_img', new_img)
cv2.waitKey()