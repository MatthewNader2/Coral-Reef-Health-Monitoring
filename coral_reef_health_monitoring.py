import cv2
import numpy as np
import os

def load_images(last_year_image_path, current_image_path):
    img1 = cv2.imread(last_year_image_path)
    img2 = cv2.imread(current_image_path)
    return img1, img2

def preprocess_image(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_image = cv2.medianBlur(gray_image, 5)
    gray_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    return gray_image

def detect_and_compute_features(image, sift):
    keypoints, descriptors = sift.detectAndCompute(image, None)
    return keypoints, descriptors

def match_features(des1, des2):
    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)
    good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]
    return good_matches

def find_homography(kp1, kp2, good_matches, min_match_count=10):
    if len(good_matches) > min_match_count:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        return M
    else:
        raise ValueError(f"Not enough matches are found - {len(good_matches)}/{min_match_count}")

def warp_image(image, homography, dimensions):
    return cv2.warpPerspective(image, homography, dimensions)

def detect_differences(img1, img2):
    diff_img = cv2.absdiff(img1, img2)
    diff_gray = cv2.cvtColor(diff_img, cv2.COLOR_BGR2GRAY)
    _, diff_thresh = cv2.threshold(diff_gray, 30, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(diff_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def draw_bounding_boxes(image, contours):
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return image

def save_image(image, path):
    cv2.imwrite(path, image)

def main(last_year_image_path, current_image_path, result_image_path):
    img1, img2 = load_images(last_year_image_path, current_image_path)
    gray1 = preprocess_image(img1)
    gray2 = preprocess_image(img2)
    
    sift = cv2.SIFT_create()
    kp1, des1 = detect_and_compute_features(gray1, sift)
    kp2, des2 = detect_and_compute_features(gray2, sift)
    
    good_matches = match_features(des1, des2)
    
    M = find_homography(kp1, kp2, good_matches)
    
    h, w = gray1.shape
    img1_aligned = warp_image(img1, M, (w, h))
    
    contours = detect_differences(img1_aligned, img2)
    result_img = draw_bounding_boxes(img2, contours)
    
    save_image(result_img, result_image_path)

if __name__ == "__main__":
    last_year_image_path = 'last_year_image.jpg'
    current_image_path = 'current_image.jpg'
    result_image_path = 'result.jpg'
    main(last_year_image_path, current_image_path, result_image_path)
