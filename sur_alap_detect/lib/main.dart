import 'package:flutter/material.dart'; // Import the Flutter material library for UI components.
import 'dart:math'; // Import the math library for mathematical functions like sin.
import 'package:just_audio/just_audio.dart'; // Import the just_audio package for audio playback.
import 'package:flutter/services.dart'; // Import services for loading assets.

// Define a StatefulWidget called MainSurfaceView.
class MainSurfaceView extends StatefulWidget {
  const MainSurfaceView({Key? key})
    : super(key: key); // Constructor for MainSurfaceView.

  @override
  State<MainSurfaceView> createState() => _MainSurfaceViewState(); // Create the state for MainSurfaceView.
}

// Define the state for MainSurfaceView.
class _MainSurfaceViewState extends State<MainSurfaceView>
    with TickerProviderStateMixin {
  // Mixin TickerProviderStateMixin for animations.
  late AnimationController
  _animationController; // Declare an AnimationController.
  List<double> _dataPoints = []; // Declare a list of doubles for graph data.
  final AudioPlayer _audioPlayer =
      AudioPlayer(); // Create an AudioPlayer instance.
  List<double> _audioData = []; // Declare a list of doubles for audio data.
  double _scrollOffset = 0.0; // Declare a double for scroll offset.
  final ScrollController _scrollController =
      ScrollController(); // Create a ScrollController.
  bool _isPlaying = false; // Declare a boolean to track if audio is playing.

  @override
  void initState() {
    super.initState(); // Call the super class initState.
    _animationController = AnimationController(
      // Initialize the AnimationController.
      vsync: this, // Provide the vsync.
      duration: const Duration(
        milliseconds: 5000,
      ), // Set the animation duration.
    )..repeat(); // Repeat the animation.

    _loadAudio(); // Call the _loadAudio function to load audio.

    _animationController.addListener(() {
      // Add a listener to the AnimationController.
      setState(() {}); // Rebuild the widget when the animation updates.
    });
  }

  // Function to load audio from assets.
  Future<void> _loadAudio() async {
    try {
      final ByteData bytes = await rootBundle.load(
        'assets/audio.mp3',
      ); // Load audio data from assets.
      final Uint8List audioBytes =
          bytes.buffer.asUint8List(); // Convert ByteData to Uint8List.
      await _audioPlayer.setAudioData(
        audioBytes,
      ); // Set the audio data in the player.

      _audioPlayer.processingStateStream.listen((processingState) {
        // Listen for processing state changes.
        if (processingState == ProcessingState.completed) {
          // If audio playback is completed.
          setState(() {
            // Rebuild the widget.
            _isPlaying = false; // Set _isPlaying to false.
          });
        }
      });

      _audioPlayer.positionStream.listen((position) {
        // Listen for position changes.
        setState(() {
          // Rebuild the widget.
          _scrollOffset =
              position.inMilliseconds.toDouble(); // Update the scroll offset.
        });
      });

      _audioPlayer.bufferPositionStream.listen((bufferPosition) {
        // Listen to buffer position changes.
        // You can use this for buffer information if needed
      });

      _audioPlayer.playerStateStream.listen((playerState) {
        // Listen to player state changes.
        setState(() {
          // Rebuild the widget.
          _isPlaying =
              playerState.playing; // Update _isPlaying based on player state.
        });
      });

      _generateAudioData(); // Generate audio data for the graph.
    } catch (e) {
      print("Error loading audio: $e"); // Print error if audio loading fails.
    }
  }

  // Function to generate audio data for the graph.
  void _generateAudioData() {
    // Replace with actual audio analysis logic.
    // This is a dummy example.
    for (int i = 0; i < 800; i++) {
      // Loop 800 times.
      _audioData.add(
        sin(i * 0.02) * 100 + 250,
      ); // Add simulated audio data to _audioData.
    }
    _dataPoints = _audioData; // Assign _audioData to _dataPoints.
  }

  @override
  void dispose() {
    _animationController.dispose(); // Dispose the AnimationController.
    _audioPlayer.dispose(); // Dispose the AudioPlayer.
    super.dispose(); // Call the super class dispose.
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      // Return a Column widget.
      children: [
        Expanded(
          // Expand the graph area.
          child: GestureDetector(
            // Wrap with GestureDetector to handle drag events.
            onHorizontalDragUpdate: (details) {
              // Handle horizontal drag updates.
              setState(() {
                // Rebuild the widget.
                _scrollOffset -=
                    details.delta.dx; // Update the scroll offset based on drag.
                if (_scrollOffset < 0)
                  _scrollOffset = 0; // Ensure scroll offset is not negative.
                if (_scrollOffset > _dataPoints.length * 5)
                  _scrollOffset =
                      _dataPoints.length *
                      5; //Ensure the scroll offset is not greater than the graph width
                _audioPlayer.seek(
                  Duration(milliseconds: _scrollOffset.toInt()),
                ); // Seek the audio player to the new position.
              });
            },
            child: SingleChildScrollView(
              // Make the graph scrollable horizontally.
              controller: _scrollController, // Assign the ScrollController.
              scrollDirection:
                  Axis.horizontal, // Set the scroll direction to horizontal.
              child: SizedBox(
                // Give the graph a specific width.
                width:
                    _dataPoints.length *
                    5, // Set the width based on data points.
                child: CustomPaint(
                  // Use CustomPaint to draw the graph.
                  painter: _GraphPainter(
                    _dataPoints,
                    _scrollOffset,
                  ), // Assign the GraphPainter.
                ),
              ),
            ),
          ),
        ),
        Row(
          // Row for audio controls and position display.
          mainAxisAlignment:
              MainAxisAlignment.center, // Center the row content.
          children: [
            IconButton(
              // Play/pause button.
              onPressed: () {
                // Handle button press.
                if (_isPlaying) {
                  // If audio is playing.
                  _audioPlayer.pause(); // Pause the audio.
                } else {
                  // If audio is paused.
                  _audioPlayer.play(); // Play the audio.
                }
              },
              icon: Icon(
                _isPlaying ? Icons.pause : Icons.play_arrow,
              ), // Set the icon based on _isPlaying.
            ),
            Text(
              'Position: ${_scrollOffset.toInt()}ms',
            ), // Display the current audio position.
          ],
        ),
      ],
    );
  }
}

// Define the GraphPainter class.
class _GraphPainter extends CustomPainter {
  final List<double> _dataPoints; // List of data points.
  final double _scrollOffset; // Scroll offset.

  _GraphPainter(
    this._dataPoints,
    this._scrollOffset,
  ); // Constructor for GraphPainter.

  @override
  void paint(Canvas canvas, Size size) {
    final paint =
        Paint() // Create a Paint object.
          ..color =
              Colors
                  .blue // Set the paint color to blue.
          ..strokeWidth = 2; // Set the paint stroke width to 2.

    final double graphWidth = size.width; // Get the graph width.
    final double graphHeight = size.height; // Get the graph height.
    final double xScale =
        graphWidth / _dataPoints.length; // Calculate the x-scale.
    double yOffset = graphHeight / 2; // Calculate the y-offset.

    final path = Path(); // Create a Path object.
    path.moveTo(0, (yOffset - _dataPoints[0])); // Move to the initial point.

    for (int i = 1; i < _dataPoints.length; i++) {
      // Loop through the data points.
      path.lineTo(
        i * xScale,
        (yOffset - _dataPoints[i]),
      ); // Draw a line to the next point.
    }

    canvas.drawPath(path, paint); // Draw the path on the canvas.
    canvas.drawLine(
      Offset(_scrollOffset, 0),
      Offset(_scrollOffset, size.height),
      Paint()
        ..color = Colors.red
        ..strokeWidth = 2,
    ); //draw the red line showing the current position.
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => true; // Repaint the graph.
}

// Main function to run the app.
void main() {
  runApp(
    const MaterialApp(
      // Run the MaterialApp.
      home: Scaffold(
        // Create a Scaffold widget.
        body: Center(
          child: MainSurfaceView(),
        ), // Center the MainSurfaceView widget.
      ),
    ),
  );
}
