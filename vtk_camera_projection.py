import vtk
import os
import sys
import numpy as np
from vtk.util import numpy_support

import cv2

def CopyMatrix4x4(matrix):
	"""
	Copies the elements of a vtkMatrix4x4 into a numpy array.

	:@type matrix: vtk.vtkMatrix4x4
	:@param matrix: The matrix to be copied into an array.
	:@rtype: numpy.ndarray
	"""
	m = np.ones((4,4))
	for i in range(4):
		for j in range(4):
			m[i,j] = matrix.GetElement(i,j)
	return m


class Camera_VTK():
	"""
	Example class showing how to project a 3D world coordinate onto a 2D image plane using VTK
	"""

	def __init__(self):
		self.timer_count = 0
		self.windowSize = 600
		self.init_vtk()
	

	def timer_callback(self,obj,event):
		"""
		Simple timer callback, called regularly to allow periodic processing 
		while interacting with the window

		:@param obj: the caller. Useful if the method is not wrapped inside a class to get VTK renderer and windows
		:@param event: the timer event which called the callback
		"""

		# Dummy sphere position
		self.shpereSource.SetCenter(10,10,10)
		shperePos = np.asarray([10,10,10,1])
	
		cam = self.renderer.GetActiveCamera()
		near, far = cam.GetClippingRange()
		w,h = self.iren.GetSize()

		# Get VTK projection matrix from camera frame to viewport coordinates
		K_c = CopyMatrix4x4(cam.GetProjectionTransformMatrix(w*1.0/h, near,far))

		# Get VTK transformation matrix from world to camera frame		
		Rt = CopyMatrix4x4(cam.GetModelViewTransformMatrix())
		
		# Shpere position in camera frame
		shpere_c = Rt.dot(shperePos).reshape((4,1))

		# Sphere position in viewport coordinates
		shpere_im = K_c.dot(shpere_c)

		# This is a required scaling, otherwise zoom parameters are not applied to the result !!
		shpere_im = shpere_im/shpere_im[-1]*self.windowSize/2.0

		# Render in VTK and continue to OpenCV display
		self.renWin.Render()

		# Convert the rendered view into an image
		winToIm = vtk.vtkWindowToImageFilter()
		winToIm.SetInput(self.renWin)
		winToIm.Update()
		vtk_image = winToIm.GetOutput()

		# convert vtk_image into an array readable by OpenCV
		height, width, _ = vtk_image.GetDimensions()
		vtk_array = vtk_image.GetPointData().GetScalars()
		components = vtk_array.GetNumberOfComponents()
		arr = cv2.flip(numpy_support.vtk_to_numpy(vtk_array).reshape(height, width, components),0)

		# Display a circle on the image at the projected position, converted into OpenCV image coordinate system
		cv2.circle(arr,(int(w*0.5 + shpere_im[0]),int(h/2.0-shpere_im[1])),10,(0,0,255),3)

		cv2.imshow('image',arr)
		cv2.waitKey(1)		

		self.timer_count += 1

	def init_vtk(self):
		"""
		Initialize VTK actors and rendering/interaction pipeline
		"""
		self.shpereSource = vtk.vtkSphereSource()
		self.shpereSource.SetCenter(10,10,10)
		self.shpereSource.SetRadius(2.0)
		self.shperemapper = vtk.vtkPolyDataMapper()
		self.shperemapper.SetInputConnection(self.shpereSource.GetOutputPort())
		self.shpereactor = vtk.vtkActor()
		self.shpereactor.SetMapper(self.shperemapper)

		self.renderer = vtk.vtkRenderer()
		self.renWin = vtk.vtkRenderWindow()
		self.iren = vtk.vtkRenderWindowInteractor()


		self.renderer.AddActor(self.shpereactor)
		self.renderer.SetBackground(0.1, 0.2, 0.4)
		self.renderer.ResetCamera()

		self.renWin.AddRenderer(self.renderer)
		self.renWin.SetSize(self.windowSize, self.windowSize)
		self.iren.SetRenderWindow(self.renWin)
		self.iren.Initialize()

		self.iren.AddObserver('TimerEvent', self.timer_callback)
		self.timerId = self.iren.CreateRepeatingTimer(100);

		self.iren.Start()


if __name__ == '__main__':
	example = Camera_VTK()
