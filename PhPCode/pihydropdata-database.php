<!--
  Rui Santos
  Complete project details at https://RandomNerdTutorials.com/cloud-weather-station-esp32-esp8266/

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files.

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
-->
<?php
  $servername = "localhost";

  // REPLACE with your Database name
  $dbname = "YOURDATABASE";
  // REPLACE with Database user
  $username = "YOURUSER";
  // REPLACE with Database user password
  $password = "YOURPASSWORD";

  function insertReading($sensor, $location, $dblvalue_raw, $value2) {
    global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "INSERT INTO SensorData (sensor, location, dblvalue_raw, value2)
    VALUES ('" . $sensor . "', '" . $location . "', '" . $dblvalue_raw . "', '" . $value2 . "')";

    if ($conn->query($sql) === TRUE) {
      return "New record created successfully";
    }
    else {
      return "Error: " . $sql . "<br>" . $conn->error;
    }
    $conn->close();
  }
  
  function getAllReadings($limit) {
    global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT id, sensor, location, dblvalue_raw, value2, reading_time FROM SensorData order by reading_time desc limit " . $limit;
    if ($result = $conn->query($sql)) {
      return $result;
    }
    else {
      return false;
    }
    $conn->close();
  }
  function getLastReadings() {
    global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT id, sensor, location, dblvalue_raw, value2, reading_time FROM SensorData order by reading_time desc limit 1" ;
    if ($result = $conn->query($sql)) {
      return $result->fetch_assoc();
    }
    else {
      return false;
    }
    $conn->close();
  }

  function minReading($limit, $value) {
     global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT MIN(" . $dblvalue_raw . ") AS min_amount FROM (SELECT " . $dblvalue_raw . " FROM SensorData order by reading_time desc limit " . $limit . ") AS min";
    if ($result = $conn->query($sql)) {
      return $result->fetch_assoc();
    }
    else {
      return false;
    }
    $conn->close();
  }

  function maxReading($limit, $value) {
     global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT MAX(" . $dblvalue_raw . ") AS max_amount FROM (SELECT " . $dblvalue_raw . " FROM SensorData order by reading_time desc limit " . $limit . ") AS max";
    if ($result = $conn->query($sql)) {
      return $result->fetch_assoc();
    }
    else {
      return false;
    }
    $conn->close();
  }

  function avgReading($limit, $value) {
     global $servername, $username, $password, $dbname;

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ($conn->connect_error) {
      die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT AVG(" . $dblvalue_raw . ") AS avg_amount FROM (SELECT " . $dblvalue_raw . " FROM SensorData order by reading_time desc limit " . $limit . ") AS avg";
    if ($result = $conn->query($sql)) {
      return $result->fetch_assoc();
    }
    else {
      return false;
    }
    $conn->close();
  }
?>
