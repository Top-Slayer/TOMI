package main

import (
	"fmt"
	"net/http"
  "path/filepath"
	"github.com/gin-gonic/gin"
)

func main() {
	fmt.Printf("http://localhost:8080/ \n\n")
	r := setupRouter()
	r.Run(":8080")
}

func setupRouter() *gin.Engine {
	r := gin.Default()
	r.POST("/upload", getDatas)

	return r
}

func getDatas(c *gin.Context) {
  file, err := c.FormFile("file")

  if err != nil {
    c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
    return
  }

  filename := filepath.Base(file.Filename)
  savePath := "./upload_images/" + filename
  if err := c.SaveUploadedFile(file, savePath); err != nil {
    c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
    return
  }

  c.JSON(http.StatusOK, gin.H{"status": "success", "filename": filename})
}
