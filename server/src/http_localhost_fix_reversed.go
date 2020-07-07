package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func httpLocalhostFixReversed(c *gin.Context) {
	fixReversedGames()
	c.String(http.StatusOK, "success\n")
}
