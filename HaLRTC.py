import cv2
import tensorly as tl
import numpy as np
from numba import jit
from line_profiler import LineProfiler

def shrinkage(X, t):
    U, Sig, VT = np.linalg.svd(X,full_matrices=False)

    Temp = np.zeros((U.shape[1], VT.shape[0]))
    for i in range(len(Sig)):
        Temp[i, i] = Sig[i]  # 生成对角阵
    Sig = Temp

    Sigt = Sig
    imSize = Sigt.shape

    for i in range(imSize[0]):
        Sigt[i, i] = np.max(Sigt[i, i] - t, 0)

    temp = np.dot(U, Sigt)
    T = np.dot(temp, VT)
    return T

@jit(nopython=True)
def ReplaceInd(X, known, Image):

    imSize = Image.shape

    for i in range(len(known)):
        in1 = int(np.ceil(known[i] / imSize[1]) - 1)
        in2 = int(imSize[0] - known[i] % imSize[1] - 1)
        X[in1, in2, :] = Image[in1, in2, :]
    return X

def init():
    KownPercentage = 0.5
    Image = cv2.imread("good_brother.jpg")
    # cv2.namedWindow('Corrupting Image', cv2.WINDOW_NORMAL)
    # cv2.imshow("Corrupting Image", Image.astype(np.uint8))
    # cv2.waitKey(0)
    imSize = Image.shape
    known = np.arange(np.prod(imSize) / imSize[2])
    np.random.shuffle(known)
    known = known[:int(KownPercentage * (np.prod(imSize) / imSize[2]))]
    print(known.shape)
    # Corrupting Image
    X = np.zeros(imSize)
    X = ReplaceInd(X, known, Image)
    cv2.namedWindow('Corrupting Image', cv2.WINDOW_NORMAL)
    cv2.imshow("Corrupting Image", X.astype(np.uint8))
    cv2.waitKey(0)
    a = abs(np.random.rand(3, 1))
    a = a / np.sum(a)
    p = 1e-6
    K = 50
    ArrSize = np.array(imSize)
    ArrSize = np.append(ArrSize, 3)
    Mi = np.zeros(ArrSize)
    Yi = np.zeros(ArrSize)
    return Image, X, known, a, Mi, Yi, imSize, ArrSize, p, K

def fuc():
    Image, X, known, a, Mi, Yi, imSize, ArrSize, p, K = init()
    for k in range(K):
        # compute Mi tensors(Step1)
        for i in range(ArrSize[3]):
            temp1 = shrinkage(tl.unfold(X, mode=i) + tl.unfold(np.squeeze(Yi[:, :, :, i]), mode=i) / p, a[i] / p)
            temp = tl.fold(temp1, i, imSize)
            Mi[:, :, :, i] = temp
        # Update X(Step2)
        X = np.sum(Mi - Yi / p, ArrSize[3]) / ArrSize[3]
        X = ReplaceInd(X, known, Image)
        # Update Yi tensors (Step 3)
        for i in range(ArrSize[3]):
            Yi[:, :, :, i] = np.squeeze(Yi[:, :, :, i]) - p * (np.squeeze(Mi[:, :, :, i]) - X)
        # Modify rho to help convergence(Step 4)
        p = 1.2 * p
    return X

lp = LineProfiler()
lp_wrapper = lp(fuc)
X = lp_wrapper()
lp.print_stats()
cv2.namedWindow('HaLRTC', cv2.WINDOW_NORMAL)
cv2.imshow("HaLRTC", X.astype(np.uint8))
cv2.waitKey()

