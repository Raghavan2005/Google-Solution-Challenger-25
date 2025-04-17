package com.raghavan.akshitma.github.shruti

import androidx.compose.ui.res.colorResource
import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons

import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.raghavan.akshitma.github.shruti.ui.theme.ShrutiTheme
import kotlinx.coroutines.delay
import kotlin.random.Random



class PlaygroundActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ShrutiTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    MicrophoneScreen(modifier = Modifier.padding(innerPadding))
                }
            }
        }
    }
}

@Composable
fun MicrophoneScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    var isRecording by remember { mutableStateOf(false) }

    // Permission launcher
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            // Start recording
            isRecording = true
            Toast.makeText(context, "Recording started", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(context, "Microphone permission is required", Toast.LENGTH_SHORT).show()
        }
    }

    Column(
        modifier = modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = "Voice Playground",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(top = 32.dp)
        )

        // Audio visualization
        if (isRecording) {
            AudioVisualization(
                modifier = Modifier
                    .height(200.dp)
                    .fillMaxWidth()
                    .padding(16.dp)
            )
        } else {
            Box(
                modifier = Modifier
                    .height(200.dp)
                    .fillMaxWidth()
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "Press the mic button to start recording",
                    textAlign = TextAlign.Center
                )
            }
        }

        // Bottom action button
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 32.dp),
            contentAlignment = Alignment.Center
        ) {
            FloatingActionButton(
                onClick = {
                    if (!isRecording) {
                        // Check and request permission
                        when {
                            ContextCompat.checkSelfPermission(
                                context,
                                Manifest.permission.RECORD_AUDIO
                            ) == PackageManager.PERMISSION_GRANTED -> {
                                isRecording = true
                                Toast.makeText(context, "Recording started", Toast.LENGTH_SHORT).show()
                            }
                            else -> {
                                permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                            }
                        }
                    } else {
                        // Stop recording
                        isRecording = false
                        Toast.makeText(context, "Recording stopped", Toast.LENGTH_SHORT).show()
                    }
                },
                containerColor = if (isRecording) Color.Red else MaterialTheme.colorScheme.primary
            ) {

            }
        }
    }
}

@Composable
fun AudioVisualization(modifier: Modifier = Modifier) {
    val barCount = 30
    var animatedBars by remember { mutableStateOf(List(barCount) { Random.nextFloat() * 0.8f + 0.2f }) }
    var frequencyHz by remember { mutableStateOf(0f) }

    LaunchedEffect(Unit) {
        while (true) {
            delay(100)
            animatedBars = List(barCount) { Random.nextFloat() * 0.8f + 0.2f }

            // Simulate frequency range between 85Hz and 1000Hz
            frequencyHz = Random.nextFloat() * (1000f - 85f) + 85f
        }
    }

    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Show frequency text
        Text(
            text = "Frequency: ${frequencyHz.toInt()} Hz",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.primary
        )
        val lineColor = colorResource(id = android.R.color.holo_blue_dark)

        // Canvas visualization
        Canvas(modifier = Modifier.fillMaxSize()) {
            val canvasWidth = size.width
            val canvasHeight = size.height
            val barWidth = canvasWidth / (barCount * 2)

            for (i in 0 until barCount) {
                val height = canvasHeight * animatedBars[i]
                val startX = i * (barWidth * 2) + barWidth / 2
                val startY = (canvasHeight + height) / 2
                val endY = (canvasHeight - height) / 2

                drawLine(
                    color = lineColor,
                    start = Offset(startX, startY),
                    end = Offset(startX, endY),
                    strokeWidth = barWidth
                )
            }
        }
    }
}

@Preview
@Composable
fun MicrophoneScreenPreview() {
    ShrutiTheme {
        MicrophoneScreen()
    }
}


//@Composable
//fun FrequencyListener(onFrequencyDetected: (Float) -> Unit) {
//    val context = LocalContext.current
//    var isRunning by remember { mutableStateOf(false) }
//
//    LaunchedEffect(Unit) {
//        if (!isRunning) {
//            isRunning = true
//            val dispatcher = AudioDispatcherFactory.fromDefaultMicrophone(22050, 1024, 0)
//            val pdh = PitchDetectionHandler { result, _ ->
//                val pitchInHz = result.pitch
//                if (pitchInHz > 0) {
//                    onFrequencyDetected(pitchInHz)
//                }
//            }
//
//            val pitchProcessor = PitchProcessor(
//                PitchEstimationAlgorithm.YIN,
//                22050f,
//                1024,
//                pdh
//            )
//            dispatcher.addAudioProcessor(pitchProcessor)
//
//            // Run in background
//            Thread { dispatcher.run() }.start()
//        }
//    }
//}

