package com.raghavan.akshitma.github.shruti

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext

class MainActivity : ComponentActivity() {


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                // Launch HomeActivity when MainActivity starts
                val context = LocalContext.current
                LaunchedEffect(Unit) {
                    val intent = Intent(context, PlaygroundActivity::class.java)
                    context.startActivity(intent)
                    (context as? ComponentActivity)?.finish()
                }

                // You can show a loading screen or splash screen here
                Text(
                    text = "Loading...",
                    modifier = Modifier.padding(innerPadding)
                )
            }

        }
    }
}

