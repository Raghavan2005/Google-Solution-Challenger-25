package com.raghavan.akshitma.github.shruti

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.activity.compose.rememberLauncherForActivityResult
import com.raghavan.akshitma.github.shruti.ui.theme.ShrutiTheme
import com.raghavan.akshitma.github.shruti.utils.MicrophoneHelper

class HomeActivity : ComponentActivity() {
    private lateinit var micHelper: MicrophoneHelper

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        micHelper = MicrophoneHelper(this)

        if (!micHelper.hasMicrophonePermission()) {
            micHelper.requestMicrophonePermission()
        } else {
            startAudioProcessing() // Your pitch detection code
        }

        enableEdgeToEdge()
        setContent {
            ShrutiTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Greeting3(
                        name = "Home",
                        modifier = Modifier.padding(innerPadding)
                    )

                    // Correctly place the AskMicrophonePermission composable inside the setContent block
                    AskMicrophonePermission {
                        startAudioProcessing()
                    }
                }
            }
        }
    }

    private fun startAudioProcessing() {
        Toast.makeText(this, "Microphone permission granted. Starting processing...", Toast.LENGTH_SHORT).show()
    }
}

@SuppressLint("ContextCastToActivity")
@Composable
fun AskMicrophonePermission(onGranted: () -> Unit) {
    val context = LocalContext.current as Activity
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = { isGranted: Boolean ->
            if (isGranted) {
                onGranted()
            } else {
                Toast.makeText(context, "Microphone permission denied", Toast.LENGTH_SHORT).show()
            }
        }
    )

    LaunchedEffect(Unit) {
        launcher.launch(Manifest.permission.RECORD_AUDIO)
    }
}

@Composable
fun Greeting3(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview3() {
    ShrutiTheme {
        Greeting3("Android")
    }
}