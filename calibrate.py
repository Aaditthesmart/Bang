import cv2, json, numpy as np

INTERNAL_CORNERS = (9, 6)    # (cols, rows) inner corners (NOT squares)
SQUARE_SIZE_M     = 0.024    # meters (e.g., 24 mm squares)
MAX_SAMPLES       = 30

objp = np.zeros((INTERNAL_CORNERS[1]*INTERNAL_CORNERS[0], 3), np.float32)
objp[:, :2] = np.mgrid[0:INTERNAL_CORNERS[0], 0:INTERNAL_CORNERS[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE_M

objpoints = []  # 3D points in world
imgpoints = []  # 2D points in image

cap = cv2.VideoCapture(0)
cv2.namedWindow("calib", cv2.WINDOW_NORMAL)

print("[i] Press SPACE to capture a view when corners are highlighted.")
print("[i] Press C to calibrate, R to reset samples, or Q/ESC to quit.")

while True:
    ok, frame = cap.read()
    if not ok: break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if hasattr(cv2, "findChessboardCornersSB"):
        ret, corners = cv2.findChessboardCornersSB(gray, INTERNAL_CORNERS, flags=cv2.CALIB_CB_EXHAUSTIVE)
        corners_vis = corners
    else:
        ret, corners = cv2.findChessboardCorners(gray, INTERNAL_CORNERS,
                                                 flags=cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
        corners_vis = corners
        if ret:
            # Subpixel refine
            term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 80, 1e-4)
            corners = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), term)

    vis = frame.copy()
    if ret:
        cv2.drawChessboardCorners(vis, INTERNAL_CORNERS, corners_vis, ret)
        cv2.putText(vis, "Corners found - press SPACE to capture", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 255, 50), 2)
    else:
        cv2.putText(vis, "Show board clearly; tilt, move, vary distance", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

    cv2.putText(vis, f"samples: {len(objpoints)}/{MAX_SAMPLES}", (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("calib", vis)
    k = cv2.waitKey(1) & 0xFF

    if k == ord(' '):
        if ret:
            objpoints.append(objp.copy())
            imgpoints.append(corners.reshape(-1,1,2))
            print(f"[+] captured {len(objpoints)} / {MAX_SAMPLES}")
        else:
            print("[-] corners not found; try again")

    elif k in (ord('c'), ord('C')) or (len(objpoints) >= MAX_SAMPLES and len(objpoints) >= 10):
        if len(objpoints) < 10:
            print("[-] Need at least ~10 good views.")
            continue
        img_size = gray.shape[::-1]  # (w,h)
        # Calibrate
        ret_cal, K, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, img_size, None, None
        )
        # Reprojection error
        tot_err = 0
        tot_pts = 0
        for i in range(len(objpoints)):
            proj, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], K, dist)
            err = cv2.norm(imgpoints[i], proj, cv2.NORM_L2)
            tot_err += err**2
            tot_pts += len(proj)
        rms = np.sqrt(tot_err / tot_pts)
        print("\n=== Calibration Results ===")
        print("K (camera matrix):\n", K)
        print("dist [k1 k2 p1 p2 k3]:\n", dist.ravel())
        print(f"RMS reprojection error (px): {rms:.3f}")

        # Save to JSON
        data = {
            "width": img_size[0], "height": img_size[1],
            "fx": float(K[0,0]), "fy": float(K[1,1]),
            "cx": float(K[0,2]), "cy": float(K[1,2]),
            "dist": dist.ravel().tolist(),
            "rms": float(rms),
            "board_cols": INTERNAL_CORNERS[0],
            "board_rows": INTERNAL_CORNERS[1],
            "square_size_m": SQUARE_SIZE_M
        }
        with open("calib.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Saved calib.json")

        # Show undistortion preview
        newK, roi = cv2.getOptimalNewCameraMatrix(K, dist, img_size, alpha=0)
        undist = cv2.undistort(frame, K, dist, None, newK)
        cv2.imshow("undistorted_preview", undist)
        cv2.waitKey(0)

    elif k in (ord('r'), ord('R')):
        objpoints.clear(); imgpoints.clear()
        print("[i] Samples reset.")
    elif k in (27, ord('q'), ord('Q')):
        break

cap.release()
cv2.destroyAllWindows()
