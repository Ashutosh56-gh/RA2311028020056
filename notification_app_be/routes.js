const express = require("express");
const router = express.Router();
const controller = require("./controller");
router.get("/top", controller.getTopNotifications);
module.exports = router;