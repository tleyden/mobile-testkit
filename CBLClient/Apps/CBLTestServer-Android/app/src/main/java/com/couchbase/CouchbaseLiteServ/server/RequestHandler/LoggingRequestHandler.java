package com.couchbase.CouchbaseLiteServ.server.RequestHandler;

import android.content.Context;

import com.couchbase.CouchbaseLiteServ.MainActivity;
import com.couchbase.CouchbaseLiteServ.server.Args;
import com.couchbase.lite.Database;
import com.couchbase.lite.LogFileConfiguration;
import com.couchbase.lite.LogLevel;

import java.io.File;

public class LoggingRequestHandler {
    /* ----------- */
    /* - Logging - */
    /* ----------- */

    public String configure(Args args){
        String log_level = args.get("log_level");
        String directory = args.get("directory");
        int maxRotateCount = args.get("max_rotate_count");
        long maxSize = args.get("max_size");
        boolean plainText = args.get("plain_text");

        if (directory.equals("")) {
            Context context = MainActivity.getAppContext();
            long ts = System.currentTimeMillis()/1000;
            directory = context.getFilesDir().getAbsolutePath() + "/logs_" + ts ;

            System.out.println("File logging configured at: " + directory.toString());
        }
        LogFileConfiguration config = new LogFileConfiguration(directory);
        if (maxRotateCount > 0) {
            config.setMaxRotateCount(maxRotateCount);
        }
        if (maxSize > 0) {
            config.setMaxSize(maxSize);
        }
        config.setUsePlaintext(plainText);
        Database.log.getFile().setConfig(config);
        if (log_level.equals("debug")) {
            Database.log.getFile().setLevel(LogLevel.DEBUG);
        } else if (log_level.equals("verbose")) {
            Database.log.getFile().setLevel(LogLevel.VERBOSE);
        } else if (log_level.equals("error")) {
            Database.log.getFile().setLevel(LogLevel.ERROR);
        } else if (log_level.equals("info")) {
            Database.log.getFile().setLevel(LogLevel.INFO);
        } else if (log_level.equals("warning")) {
            Database.log.getFile().setLevel(LogLevel.WARNING);
        } else {
            Database.log.getFile().setLevel(LogLevel.NONE);
        }
        return directory;
    }

    public boolean getPlainTextStatus(Args args) {
        return Database.log.getFile().getConfig().usesPlaintext();
    }

    public int getMaxRotateCount(Args args) {
        return Database.log.getFile().getConfig().getMaxRotateCount();
    }

    public long getMaxSize(Args args) {
        return Database.log.getFile().getConfig().getMaxSize();
    }

    public String getDirectory(Args args) {
        return Database.log.getFile().getConfig().getDirectory();
    }

    public int getLogLevel(Args args) {
        return Database.log.getFile().getLevel().getValue();
    }

    public LogFileConfiguration getConfig(Args args) {
        return Database.log.getFile().getConfig();
    }
    
}
